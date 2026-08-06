from chromadb import PersistentClient

from config import Settings
from rag.embeddings import EmbeddingModel
from rag.models import DocumentChunk


class VectorStore:

    def __init__(self) -> None:

        self.client = PersistentClient(path=Settings.CHROMA_DIRECTORY)

        self.collection = self.client.get_or_create_collection(
            name=Settings.CHROMA_COLLECTION,
            metadata={"description": "ESG Knowledge Base"},
        )

    def add_documents(
        self,
        chunks: list[DocumentChunk],
    ) -> None:

        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]

        embeddings = EmbeddingModel.embed_documents(texts)

        ids = [f"{chunk.source}_{chunk.page}_{chunk.chunk_id}" for chunk in chunks]

        metadatas = [
            {
                **chunk.metadata,
                "source": chunk.source,
                "page": chunk.page,
                "document_type": chunk.document_type,
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def count(self) -> int:

        return self.collection.count()

    def reset(self) -> None:

        self.client.delete_collection(Settings.CHROMA_COLLECTION)

        self.collection = self.client.get_or_create_collection(
            Settings.CHROMA_COLLECTION
        )
