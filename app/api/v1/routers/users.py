from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from redis.asyncio import Redis

from app.core.extensions import UserNotFoundError, InvalidPasswordError
from app.application.services.user_service import UserService, AuthService
from app.application.dependencies import get_uow, get_redis_repository, get_current_user
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.core.security import SecurityUtils
from app.application.dto.identity import UserCreateDTO, UserResponseDTO, LoginDTO, UserProfileUpdateDTO
from app.application.dto.tokens import TokenResponseDTO, RefreshTokenDTO


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post(
    path="/register", 
    response_model=UserResponseDTO,
    status_code=status.HTTP_201_CREATED
)
async def create_user(dto: UserCreateDTO, uow: IUnitOfWork = Depends(get_uow)):
    service = UserService(uow)
    try:
        user = await service.create_user(
            username=dto.username,
            password_hash=SecurityUtils.hash_password(dto.password),
            phone=dto.phone,
            telegram_id=dto.telegram_id,
            profile=dto.profile.to_domain()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return UserResponseDTO.model_validate(user)


@router.post(
    path="/login",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_200_OK
)
async def login(
    dto: LoginDTO,
    redis: Redis = Depends(get_redis_repository),
    uow: IUnitOfWork = Depends(get_uow)
):
    service = AuthService(uow, redis)
    try:
        return await service.login(dto)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except InvalidPasswordError:
        raise HTTPException(status_code=401, detail="Неверный пароль")


@router.get(
    path="/telegram/{telegram_id}",
    response_model=UserResponseDTO,
    status_code=status.HTTP_200_OK
)
async def get_user_by_telegram_id(
    telegram_id: int,
    current_user = Depends(get_current_user),
    uow: IUnitOfWork = Depends(get_uow)
):
    service = UserService(uow)
    user = await service.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponseDTO.model_validate(user)


@router.get(
    path="/exists/phone/{phone}",
    response_model=bool,
    status_code=status.HTTP_200_OK
)
async def exists_by_phone(
    phone: str,
    current_user = Depends(get_current_user),
    uow: IUnitOfWork = Depends(get_uow)
):
    service = UserService(uow)
    return await service.check_phone(phone)


@router.post(
    path="/refresh",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_200_OK
)
async def refresh(
    dto: RefreshTokenDTO,
    uow: IUnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis_repository)
):
    service = AuthService(uow, redis)
    return await service.refresh(dto.refresh_token)


@router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    current_user = Depends(get_current_user),
    uow: IUnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis_repository)
):
    service = AuthService(uow, redis)
    await service.logout(user_id=str(current_user.id))


@router.get(
    path="/{user_id}",
    response_model=UserResponseDTO,
    status_code=status.HTTP_200_OK
)
async def get_user(
    user_id: UUID,
    current_user = Depends(get_current_user),
    uow: IUnitOfWork = Depends(get_uow)
):
    service = UserService(uow)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponseDTO.model_validate(user)


@router.patch(
    path="/profile",
    response_model=UserResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    dto: UserProfileUpdateDTO,
    current_user = Depends(get_current_user),
    uow: IUnitOfWork = Depends(get_uow)
):
    service = UserService(uow)
    try:
        user = await service.update_profile(user_id=current_user.id, dto=dto)
        return UserResponseDTO.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))