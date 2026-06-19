from uuid import UUID, uuid4
from dataclasses import dataclass, field


@dataclass
class KnowledgeChunk:
    document_id: UUID
    chunk_index: int
    content: str
    embedding: list[float]
    token_count: int
    content_hash: str
    meta: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)