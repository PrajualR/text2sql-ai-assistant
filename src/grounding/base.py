from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GroundingResult:
    context: str
    matched_terms: list[str]
    columns: list[str]


class GroundingRetriever(ABC):

    @abstractmethod
    def retrieve(self, question: str) -> GroundingResult:
        """Resolve business terminology into database grounding."""
        raise NotImplementedError
