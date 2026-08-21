import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Centralized application configuration.

    All configurable values should be defined here rather than being
    scattered throughout the project.
    """

    # ==========================================================
    # GROQ
    # ==========================================================

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # ==========================================================
    # LLM
    # ==========================================================

    LLM_MODEL = os.getenv(
        "LLM_MODEL",
        "openai/gpt-oss-120b",
    )

    LLM_TEMPERATURE = float(
        os.getenv(
            "LLM_TEMPERATURE",
            0,
        )
    )

    LLM_MAX_TOKENS = int(
        os.getenv(
            "LLM_MAX_TOKENS",
            1024,
        )
    )

    LLM_TIMEOUT = int(
        os.getenv(
            "LLM_TIMEOUT",
            60,
        )
    )

    LLM_MAX_RETRIES = int(
        os.getenv(
            "LLM_MAX_RETRIES",
            2,
        )
    )

    # ==========================================================
    # EMBEDDINGS
    # ==========================================================

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "BAAI/bge-base-en-v1.5",
    )

    # ==========================================================
    # CHROMA
    # ==========================================================

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    CHROMA_DIRECTORY = os.getenv(
        "CHROMA_DIRECTORY",
        str(PROJECT_ROOT / "chroma_db"),
    )

    CHROMA_COLLECTION = os.getenv(
        "CHROMA_COLLECTION",
        "esg_knowledge",
    )

    # ==========================================================
    # RETRIEVAL
    # ==========================================================

    TOP_K = int(
        os.getenv(
            "TOP_K",
            5,
        )
    )

    # ==========================================================
    # CHUNKING
    # ==========================================================

    CHUNK_SIZE = int(
        os.getenv(
            "CHUNK_SIZE",
            800,
        )
    )

    CHUNK_OVERLAP = int(
        os.getenv(
            "CHUNK_OVERLAP",
            150,
        )
    )
