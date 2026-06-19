from io import BytesIO
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.application.interfaces.text_splitter import ITextSplitterService

class LangChainPdfSplitterService(ITextSplitterService):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 200):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap
        )


    def split_pdf(self, pdf_bytes: bytes) -> list[str]:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        full_text = "\n".join(pages_text)

        return self._splitter.split_text(full_text)