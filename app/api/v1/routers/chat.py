from uuid import UUID
from starlette import status
from fastapi import APIRouter, Depends, status

from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.application.interfaces.llm import ILLMService
from app.application.dto.for_ai import ChatRequest, ChatResponse
from app.application.services.chat_service import ChatService
from app.application.dependencies import (
    get_uow, 
    get_embedding_service, 
    get_llm_service,
    get_current_user
)


router = APIRouter(prefix="/api/v1/chat")


@router.post(
    path="/ask",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
async def ask_ai(
    dto: ChatRequest,
    uow: IUnitOfWork = Depends(get_uow),
    embedder: SentenceTransformerEmbeddingService = Depends(get_embedding_service),
    llm_service: ILLMService = Depends(get_llm_service),
    current_user = Depends(get_current_user)
):
    service = ChatService(uow, embedder, llm_service)
    response = await service.answer_question(current_user.id, dto.message)

    return response