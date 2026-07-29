import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


class LLMClient:
    """Factory for creating the Groq LLM."""

    @staticmethod
    def get_llm() -> ChatGroq:
        """
        Returns a configured ChatGroq instance.
        """

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Please check your .env file.")

        return ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=1024,
            timeout=60,
            max_retries=2,
        )


llm = LLMClient.get_llm()
