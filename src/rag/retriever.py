from config import Settings
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore


class Retriever:
    """
    Performs semantic search against the ESG knowledge base.
    """

    def __init__(self) -> None:

        self.vector_store = VectorStore()

    def retrieve(
        self,
        query: str,
    ) -> list[dict]:

        embedding = EmbeddingModel.embed_query(query)

        company_results = self.vector_store.collection.query(
            query_embeddings=[embedding],
            n_results=3,
            where={"document_type": "company"},
        )

        standards_results = self.vector_store.collection.query(
            query_embeddings=[embedding],
            n_results=2,
            where={"document_type": "standards"},
        )

        retrieved_chunks = []

        retrieved_chunks.extend(self._parse_results(company_results))

        retrieved_chunks.extend(self._parse_results(standards_results))
        retrieved_chunks.sort(
            key=lambda x: x["score"],
            reverse=True,
        )
        return retrieved_chunks

    @staticmethod
    def _parse_results(results) -> list[dict]:

        chunks = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):

            chunks.append(
                {
                    "content": document,
                    "metadata": metadata,
                    "score": round(1 - distance, 4),
                }
            )

        return chunks

    @staticmethod
    def build_context(
        retrieved_chunks: list[dict],
    ) -> str:

        if not retrieved_chunks:
            return "No relevant knowledge found."

        context = []

        for i, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):

            metadata = chunk["metadata"]

            context.append(f"""Document {i}
                Source: {metadata["source"]}
                Document Type: {metadata["document_type"]}
                Page: {metadata["page"]}

                {chunk["content"]}
                """)

        return "\n\n".join(context)
