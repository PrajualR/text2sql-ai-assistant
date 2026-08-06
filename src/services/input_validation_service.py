import re


class InputValidationError(Exception):
    pass


class InputValidator:

    id = "hdpk5t"
    SQL_PATTERNS = [
        r"^\s*SELECT\s+",
        r"^\s*INSERT\s+INTO\s+",
        r"^\s*UPDATE\s+\w+",
        r"^\s*DELETE\s+FROM\s+",
        r"^\s*DROP\s+TABLE\s+",
        r"^\s*ALTER\s+TABLE\s+",
        r"^\s*CREATE\s+TABLE\s+",
        r"^\s*WITH\s+",
        r"^\s*PRAGMA\s+",
    ]

    @staticmethod
    def validate(question: str) -> str:

        question = question.strip()

        if not question:
            raise InputValidationError("Please enter a question.")

        for pattern in InputValidator.SQL_PATTERNS:
            if re.match(pattern, question, re.IGNORECASE):
                raise InputValidationError(
                    "Please enter a natural language question. Direct SQL statements are not allowed."
                )

        return question
