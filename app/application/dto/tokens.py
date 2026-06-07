from pydantic import BaseModel


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str

    class Config:
        from_attributes = True


class RefreshTokenDTO(BaseModel):
    refresh_token: str