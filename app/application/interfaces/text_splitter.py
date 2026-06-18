from abc import ABC, abstractmethod

class ITextSplitterService(ABC):
    @abstractmethod
    def split_pdf(self, pdf_bytes: bytes) -> list[str]:
        pass