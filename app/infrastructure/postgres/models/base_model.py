from app.infrastructure.postgres.database import Base

class BaseModel(Base):
    __abstract__ = True