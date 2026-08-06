from sentence_transformers import SentenceTransformer

from config import Settings


class EmbeddingModel:
    """
    Generates dense vector embeddings for document chunks
    and user queries.

    A single model instance is shared across the application.
    """

    MODEL_NAME = Settings.EMBEDDING_MODEL
    _model = None

    @classmethod
    def model(cls) -> SentenceTransformer:

        if cls._model is None:

            cls._model = SentenceTransformer(cls.MODEL_NAME)

        return cls._model

    @classmethod
    def embed_documents(
        cls,
        texts: list[str],
    ) -> list[list[float]]:

        return (
            cls.model()
            .encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            .tolist()
        )

    @classmethod
    def embed_query(
        cls,
        query: str,
    ) -> list[float]:

        return (
            cls.model()
            .encode(
                query,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            .tolist()
        )
