from uuid import UUID, uuid4
from fastapi import UploadFile
from typing import Callable, AsyncContextManager

from app.domain.knowledge.document import Document
from app.domain.knowledge.chunk import KnowledgeChunk
from app.domain.enums import KnowledgeDocumentStatus
from app.application.interfaces.object_storage import IObjectStorage
from app.application.interfaces.unit_of_work import IUnitOfWork


class DocumentUploadService:
    def __init__(
        self,
        storage: IObjectStorage,
        uow_factory: Callable[[], AsyncContextManager[IUnitOfWork]]
    ):
        self._storage = storage
        self._uow_factory = uow_factory


    async def upload_pdf(self, file: UploadFile, user_id: UUID) -> UUID:
        content = await file.read()
        object_name = f"{user_id}/{uuid4()}"

        await self._storage.upload(
            bucket="knowledge",
            object_name=object_name,
            data=content
        )

        async with self._uow_factory() as uow:
            document = Document(
                title=file.filename,
                filename=file.filename,
                bucket="knowledge",
                object_name=object_name,
                uploaded_by=user_id,
                status=KnowledgeDocumentStatus.UPLOADED.value,
            )

            await uow.knowledge_documents.save(document)
            await uow.commit()

        return document.id
