from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.application.services.user_service import UserService
from app.api.v1.dependencies import get_uow
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.infrastructure.security.password import hash_password 
from app.application.dto.identity import UserCreateDTO, UserResponseDTO


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post(
    path="/", 
    response_model=UserResponseDTO,
    status_code=HTTP_201_CREATED
)
async def create_user(dto: UserCreateDTO, uow: IUnitOfWork = Depends(get_uow)):
    service = UserService(uow)
    try:
        user = await service.create_user(
            username=dto.username,
            password_hash=hash_password(dto.password),
            profile=dto.profile.to_domain()
        )
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    
    return UserResponseDTO.model_validate(user)


@router.get(
    path="/{user_id}",
    response_model=UserResponseDTO,
    status_code=HTTP_200_OK
)
async def get_user(user_id: UUID, uow: IUnitOfWork = Depends(get_uow)):
    service = UserService(uow)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponseDTO.model_validate(user)