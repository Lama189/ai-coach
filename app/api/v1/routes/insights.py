from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.application.services.insight_service import InsightService
from app.application.dependencies import get_uow, get_embedding_service, get_current_user
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.application.dto.identity import CreateInsightDTO, InsightResponseDTO


router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


@router.post(
    path="/",
    response_model=InsightResponseDTO,
    status_code=status.HTTP_201_CREATED
)
async def create_insight(
    dto: CreateInsightDTO,
    current_user = Depends(get_current_user),
    uow: IUnitOfWork = Depends(get_uow),
    embedder: SentenceTransformerEmbeddingService = Depends(get_embedding_service)
):
    service = InsightService(uow, embedder)
    try:
        insight = await service.create_insight(current_user.id, dto)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return InsightResponseDTO.model_validate(insight)