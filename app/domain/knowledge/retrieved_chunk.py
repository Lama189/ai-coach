from dataclasses import dataclass

from app.domain.knowledge.chunk import KnowledgeChunk


@dataclass
class RetrievedChunk:
    chunk: KnowledgeChunk
    similarity: float
