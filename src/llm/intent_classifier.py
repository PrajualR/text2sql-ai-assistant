from langchain_core.output_parsers import StrOutputParser

from llm.client import llm
from llm.prompts import INTENT_PROMPT


class IntentClassificationError(Exception):
    """Raised when intent classification fails."""


class IntentClassifier:
    """Classifies a user message as READ, WRITE, or OFF_TOPIC."""

    VALID_INTENTS = {"READ", "WRITE", "OFF_TOPIC"}

    @classmethod
    def classify(cls, question: str) -> str:
        """
        Classify a user's message.

        Args:
            question: Natural language input.

        Returns:
            READ, WRITE, or OFF_TOPIC

        Raises:
            IntentClassificationError
        """

        chain = INTENT_PROMPT | llm | StrOutputParser()

        try:
            intent = chain.invoke({"question": question}).strip().upper()

        except Exception as exc:
            raise IntentClassificationError(
                f"Intent classification failed: {exc}"
            ) from exc

        if intent not in cls.VALID_INTENTS:
            raise IntentClassificationError(f"Invalid intent returned by LLM: {intent}")

        return intent