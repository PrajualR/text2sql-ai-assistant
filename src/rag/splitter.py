from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Settings
from rag.models import DocumentChunk


class DocumentSplitter:
    """
    Splits PDF pages into semantically meaningful chunks.

    Each output chunk preserves:
        - source document
        - page number
        - document type
        - metadata
    """

    def __init__(
        self,
        chunk_size: int = Settings.CHUNK_SIZE,
        chunk_overlap: int = Settings.CHUNK_OVERLAP,
    ):

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def split(
        self,
        pages: list[dict],
    ) -> list[DocumentChunk]:

        chunks = []

        chunk_id = 1

        for page in pages:

            pieces = self._splitter.split_text(page["text"])

            for piece in pieces:

                chunks.append(
                    DocumentChunk(
                        text=piece,
                        source=page["source"],
                        page=page["page"],
                        chunk_id=chunk_id,
                        document_type=page["document_type"],
                        metadata=page["metadata"],
                    )
                )

                chunk_id += 1

        return chunks
