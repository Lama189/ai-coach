from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.application.services.ai_service import AIService
from app.application.services.program_service import WorkoutProgramService

from app.application.dependencies import (
    get_uow, 
    get_llm_api_key, 
    get_embedding_service
)
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.dto.program import (
    WorkoutProgramCreate, 
    WorkoutProgramResponse, 
    GenerateProgram, 
    TaskAcceptedResponse
)
from app.application.workers.tasks import generate_workout_task


router = APIRouter(prefix="/api/v1/programs", tags=["programs"])


@router.post(
    path="/",
    response_model=WorkoutProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать программу тренировок вручную",
    description="Создаёт программу тренировок из готовых данных без участия AI."
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
    path="/generate",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Сгенерировать персональную программу через AI",
    description="""
            Запускает асинхронную генерацию персональной программы тренировок через AI-агента.

            Агент:
            1. Ищет подходящие упражнения в базе данных
            2. Создаёт недостающие упражнения если нужно
            3. Составляет программу с учётом профиля и пожеланий пользователя

            Возвращает `task_id` — используй его для отслеживания статуса задачи.
                """,
)
async def generate_workout_program(
    dto: GenerateProgram, 
):
    try:
        task_id = str(uuid4())
        task_payload = dto.model_dump()

        generate_workout_task.apply_async(
            kwargs={
                "dto_dict": task_payload, 
                "task_id": task_id  
            },
            task_id=task_id 
        )

        return TaskAcceptedResponse(task_id=task_id, status="processing")
    
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue task: {str(e)}"
        )
    

@router.get(
    path="/{user_id}",
    response_model=WorkoutProgramResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить активную программу пользователя",
    description="Возвращает текущую активную программу тренировок для указанного пользователя.",
)
async def get_program_by_user_id(user_id: UUID, uow: IUnitOfWork = Depends(get_uow)):
    service = WorkoutProgramService(uow)
    try:
        program = await service.get_actual_program_for_user(user_id)
        return WorkoutProgramResponse.model_validate(program)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )