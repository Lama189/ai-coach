from uuid import UUID, uuid4
from dataclasses import dataclass, field

from app.domain.enums import KnowledgeDocumentStatus


@dataclass
class Document:
    title: str
    filename: str
    bucket: str
    object_name: str
    uploaded_by: UUID
    status: KnowledgeDocumentStatus
    id: UUID = field(default_factory=uuid4)
