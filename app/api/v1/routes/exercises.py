from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.services.exercise_service import ExerciseService
from app.api.v1.dependencies import get_uow
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.infrastructure.security.password import hash_password 
from app.application.dto.training import CreateExerciseDTO, ExerciseResponseDTO


router = APIRouter(prefix="/api/v1/exercises", tags=["exercises"])


@router.post(
    path="/",
    response_model=ExerciseResponseDTO,
    status_code=HTTP_201_CREATED
)
async def create_exercise(dto: CreateExerciseDTO, uow: IUnitOfWork = Depends(get_uow)):
    service = ExerciseService(uow)
    try:
        exercise = await service.create_exercise(
            name=dto.name,
            muscle_group=dto.muscle_group,
            description=dto.description
        )
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    
    return ExerciseResponseDTO.model_validate(exercise)