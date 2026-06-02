from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.application.services.ai_service import AIService
from app.application.services.program_service import WorkoutProgramService

from app.api.v1.dependencies import (
    get_uow, 
    get_llm_api_key, 
    get_embedding_service
)
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.dto.program import WorkoutProgramCreate, WorkoutProgramResponse


router = APIRouter(prefix="/api/v1/programs", tags=["programs"])


@router.post(
    path="/",
    response_model=WorkoutProgramResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_workout_program(dto: WorkoutProgramCreate, uow: IUnitOfWork = Depends(get_uow)):
    service = WorkoutProgramService(uow)
    try:
        return await service.create_program(dto)
     
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.post(
    path="/generate/{user_id}",
    response_model=WorkoutProgramResponse,
    status_code=status.HTTP_201_CREATED
)
async def generate_workout_program(
    user_id: UUID, 
    uow: IUnitOfWork = Depends(get_uow),
    embedder: SentenceTransformerEmbeddingService = Depends(get_embedding_service),
    api_key: str = Depends(get_llm_api_key)
):
    service = AIService(uow, embedder, api_key)
    try:
        return await service.generate_workout(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )