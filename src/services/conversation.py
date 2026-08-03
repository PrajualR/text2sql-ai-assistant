from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    question: str
    sql: str


@dataclass
class ConversationContext:
    """Holds the last N turns of a session so follow-up / drill-down
    questions can be resolved against prior SQL."""

    turns: list[ConversationTurn] = field(default_factory=list)
    max_turns: int = 5

    def add(self, question: str, sql: str) -> None:
        self.turns.append(ConversationTurn(question=question, sql=sql))
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    def as_prompt_text(self) -> str:
        if not self.turns:
            return "No prior conversation in this session."
        lines = []
        for i, turn in enumerate(self.turns, start=1):
            lines.append(f"Turn {i} Question: {turn.question}")
            lines.append(f"Turn {i} SQL: {turn.sql}")
        return "\n".join(lines)

    def combined_text(self) -> str:
        """Used only by the deterministic topic filter, so a bare
        follow-up like 'drill into Singapore' isn't rejected as
        off-topic just because it has no domain vocabulary of its own."""
        return " ".join(t.question for t in self.turns)

    def clear(self) -> None:
        self.turns.clear()

    def __bool__(self) -> bool:
        return bool(self.turns)