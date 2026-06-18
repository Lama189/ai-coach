from uuid import UUID
from app.application.dto.for_ai import ChatResponse, ChunkResponseDTO
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.interfaces.llm import ILLMService
from app.application.interfaces.unit_of_work import IUnitOfWork


class ChatService:
    def __init__(
        self, 
        uow: IUnitOfWork,
        embedder: SentenceTransformerEmbeddingService,
        llm_service: ILLMService
    ) -> None:
        self._uow = uow
        self._embedder = embedder
        self._llm_service = llm_service


    async def answer_question(self, user_id: UUID, user_message: str) -> ChatResponse:
        context_text = "Дополнительный контекст из базы знаний не найден"
        sources_dto: list[ChunkResponseDTO] = []

        query_vector = await self._embedder.get_embedding(user_message)

        similar_chunks = await self._uow.knowledge_chunks.search_similar(
            embedding=query_vector,
            limit=5,
            min_similarity=0.6
        )

        if similar_chunks:
            ordered_chunks = sorted(list(similar_chunks), key=lambda x: x.chunk_index)
            
            context_text = "\n\n".join([
                f"[Чанк {chunk.chunk_index}]: {chunk.content}" 
                for chunk in ordered_chunks
            ])

            sources_dto = [
                ChunkResponseDTO(
                    chunk_index=chunk.chunk_index,
                    document_name=chunk.meta.get("filename", "Анатомия упражнений")
                )
                for chunk in ordered_chunks
            ]

        ai_text_answer = await self._llm_service.generate(
            user_message=user_message,
            context_text=context_text
        )

        return ChatResponse(
            answer=ai_text_answer,
            sources=sources_dto
        )