from dataclasses import dataclass


@dataclass(slots=True)
class DocumentChunk:
    """
    Represents a single chunk stored in the vector database.

    Each chunk contains:
        - text used for embedding
        - document metadata
        - page number
        - chunk number within the page
    """

    text: str

    source: str
    page: int
    chunk_id: int

    document_type: str

    metadata: dict
