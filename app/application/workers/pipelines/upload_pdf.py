import logging
from uuid import UUID
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import asyncio
import hashlib
import tiktoken
from io import BytesIO

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


from app.domain.enums import KnowledgeDocumentStatus
from app.domain.knowledge.chunk import KnowledgeChunk
from app.domain.knowledge.document import Document

from app.infrastructure.storage.minio_storage import MinioStorage
from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.infrastructure.storage.client import get_minio_client
from app.infrastructure.postgres.database import build_worker_session_maker
from app.infrastructure.logging.decorators import log_duration


logger = logging.getLogger(__name__)


def _split_to_chunks(pdf_bytes: bytes) -> list[str]:
    pdf_file = BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)

    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=200
    )

    chunks = text_splitter.split_text(full_text)
    return chunks


def calculate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


async def _async_process_pdf_pipeline(task_id: str, user_id: str, bucket_name: str, object_name: str):
    minio_client = get_minio_client()
    minio_storage = MinioStorage(minio_client)
    
    try:
        pdf_bytes, filename = await minio_storage.download(bucket_name, object_name)
        if not filename:
            filename = object_name.split("/")[-1]
    except Exception as e:
        logger.error("Failed to download PDF from MinIO: %s", e)
        raise e

    chunks = _split_to_chunks(pdf_bytes)
    document = Document(
        title=filename,
        filename=filename,
        bucket=bucket_name,
        object_name=object_name,
        uploaded_by=UUID(user_id),  
        status=KnowledgeDocumentStatus.PROCESSING,
    )

    embedder = SentenceTransformerEmbeddingService()
    knowledge_chunks = []

    for index, chunk_text in enumerate(chunks):
        vector = await embedder.get_embedding(chunk_text)

        chunk_domain = KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk_text,
            embedding=vector,
            token_count=count_tokens(chunk_text),
            content_hash=calculate_hash(chunk_text),
            meta={"task_id": task_id},
        )
        knowledge_chunks.append(chunk_domain)

    session_maker, worker_engine = build_worker_session_maker()

    @asynccontextmanager
    async def uow_factory() -> AsyncGenerator[PostgresUnitOfWork, None]:
        async with PostgresUnitOfWork(session_maker()) as uow:
            yield uow

    try:
        async with uow_factory() as uow:
            await uow.knowledge_documents.save(document)

            for chunk in knowledge_chunks:
                await uow.knowledge_chunks.save(chunk)

            document.status = KnowledgeDocumentStatus.PROCESSED
            await uow.knowledge_documents.save(document) 

            await uow.commit()
            
    except Exception as e:
        logger.error("Failed to save document to database: %s", e)
        try:
            async with uow_factory() as uow:
                document.status = KnowledgeDocumentStatus.FAILED
                await uow.knowledge_documents.save(document)
                await uow.commit()
        except Exception as inner_e:
            logger.error("Failed to save FAILED status: %s", inner_e)
        raise e
        
    finally:
        await worker_engine.dispose()

    return len(knowledge_chunks)


@log_duration
async def process_pdf_task(
    task_id: str, user_id: str, bucket_name: str, object_name: str
):
    return await _async_process_pdf_pipeline(
        task_id, user_id, bucket_name, object_name
    )