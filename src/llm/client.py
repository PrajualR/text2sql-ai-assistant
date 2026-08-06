from langchain_groq import ChatGroq

from config import Settings


class LLMClient:
    """
    Factory for creating the application's LLM.
    """

    @staticmethod
    def get_llm() -> ChatGroq:

        if not Settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Please check your .env file.")

        return ChatGroq(
            api_key=Settings.GROQ_API_KEY,
            model=Settings.LLM_MODEL,
            temperature=Settings.LLM_TEMPERATURE,
            max_tokens=Settings.LLM_MAX_TOKENS,
            timeout=Settings.LLM_TIMEOUT,
            max_retries=Settings.LLM_MAX_RETRIES,
        )


llm = LLMClient.get_llm()
