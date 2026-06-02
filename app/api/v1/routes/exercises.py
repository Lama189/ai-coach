from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.application.services.exercise_service import ExerciseService
from app.api.v1.dependencies import get_uow, get_embedding_service
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.application.dto.training import CreateExerciseDTO, ExerciseResponseDTO


router = APIRouter(prefix="/api/v1/exercises", tags=["exercises"])


@router.post(
    path="/",
    response_model=ExerciseResponseDTO,
    status_code=HTTP_201_CREATED
)
async def create_exercise(
    dto: CreateExerciseDTO, 
    uow: IUnitOfWork = Depends(get_uow),
    embedder: SentenceTransformerEmbeddingService = Depends(get_embedding_service)
):
    service = ExerciseService(uow, embedder)
    try:
        exercise = await service.create_exercise(
            name=dto.name,
            muscle_group=dto.muscle_group,
            description=dto.description
        )
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    
    return ExerciseResponseDTO.model_validate(exercise)