from grounding.base import GroundingResult
from rag.retriever import Retriever


class EmbeddingGroundingRetriever:
    """
    Adapter for the existing Chroma-based retriever.

    The underlying embedding retrieval behavior is unchanged.
    """

    def __init__(self) -> None:
        self.retriever = Retriever()

    def retrieve(
        self,
        question: str,
    ) -> GroundingResult:

        retrieved_chunks = self.retriever.retrieve(question)

        context = self.retriever.build_context(retrieved_chunks)

        return GroundingResult(
            context=context,
            matched_terms=[],
            columns=[],
        )
