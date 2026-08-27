class UnsupportedQuestionError(Exception):
    """
    Raised when a question is understood but cannot be answered by this
    assistant — off-topic, a write/DDL request, empty input, or a
    question the LLM determined is outside the ESG schema's scope
    (UNSUPPORTED_QUERY). This is an EXPECTED outcome, not a failure.

    Every raise site for this exception uses fixed, curated, user-safe
    text — never text built from or interpolating a caught lower-level
    exception. Callers may safely display str(exc) directly to the user.
    """
