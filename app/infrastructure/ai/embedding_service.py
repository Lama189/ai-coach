import asyncio

from sentence_transformers import SentenceTransformer
from app.domain.interfaces.embedding import IEmbeddingService

class SentenceTransformerEmbeddingService(IEmbeddingService):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)

    
    async def get_embedding(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._get_embedding_sync, text)


    def _get_embedding_sync(self, text: str) -> list[float]:
        clean_text = text.strip()
        embedding = self._model.encode(clean_text)
        return embedding.tolist()