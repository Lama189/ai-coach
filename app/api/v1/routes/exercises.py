from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.application.services.exercise_service import ExerciseService
from app.application.dependencies import get_uow, get_embedding_service
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.application.dto.training import CreateExerciseDTO, ExerciseResponseDTO


router = APIRouter(prefix="/api/v1/exercises", tags=["exercises"])


@router.post(
    path="/",
    response_model=ExerciseResponseDTO,
    status_code=status.HTTP_201_CREATED
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return ExerciseResponseDTO.model_validate(exercise)


@router.delete(
    path="/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_exercise(
    exercise_id: UUID,
    uow: IUnitOfWork = Depends(get_uow),
    embedder: SentenceTransformerEmbeddingService = Depends(get_embedding_service)
):
    service = ExerciseService(uow, embedder)
    try:
        await service.delete_exercise(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))