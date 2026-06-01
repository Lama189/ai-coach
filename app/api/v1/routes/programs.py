from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.services.program_service import WorkoutProgramService
from app.api.v1.dependencies import get_uow
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.infrastructure.security.password import hash_password 
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
        program = await service.create_program(dto)

        return program
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )