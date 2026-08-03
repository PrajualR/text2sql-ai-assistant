import re

# Vocabulary of terms that a genuine ESG-data question would plausibly
# contain. This is intentionally broad (schema field names plus common
# synonyms/domain terms) rather than an exact match against column
# names, so paraphrased legitimate questions ("carbon footprint",
# "gender diversity") still pass.
#
# This exists as a deterministic backstop, independent of the LLM.
# Testing showed that relying solely on prompted LLM judgment (intent
# classification + SQL generation's UNSUPPORTED_QUERY fallback) was not
# reliable enough on its own: a compliant model under uncertainty would
# sometimes generate a disconnected fallback query (e.g. "SELECT ...
# LIMIT 1") for greetings/off-topic input rather than admitting it
# couldn't answer. This filter catches clearly off-topic input before
# any LLM call is made, cheaply and deterministically.
_DOMAIN_VOCABULARY = {
    # entities / dimensions
    "facility", "facilities", "plant", "plants", "site", "sites",
    "country", "countries", "city", "cities", "industry", "industries",
    "year", "years", "fiscal",
    # emissions / environment
    "emission", "emissions", "scope", "scope1", "scope2", "scope3",
    "carbon", "footprint", "ghg", "greenhouse",
    "energy", "renewable", "mwh", "kwh",
    "water", "withdrawal", "recycled", "recycling",
    "waste", "landfill",
    # workforce / social
    "employee", "employees", "workforce", "female", "gender",
    "diversity", "turnover", "training", "headcount", "staff",
    # governance
    "compliance", "violation", "violations", "audit", "governance",
    "esg",
    # generic analytical verbs (only count if paired with something
    # else, but harmless to include since "show trends" alone without
    # a domain noun is still ambiguous — kept for completeness)
    "compare", "trend", "trends", "average", "highest", "lowest",
    "top", "bottom", "total", "sum", "count",
    # generic database/write-action vocabulary — WRITE-style commands
    # ("create a table", "delete records") often don't mention any
    # ESG domain noun at all, so these need to be recognized here too
    # or they'd be misrouted to the OFF_TOPIC message instead of the
    # more accurate "this is read-only" WRITE message. Either message
    # blocks the request, but this keeps the wording accurate.
    "table", "tables", "database", "record", "records", "row", "rows",
    "column", "columns", "insert", "update", "delete", "remove",
    "drop", "alter", "truncate", "modify", "edit",
}

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def is_plausibly_domain_related(question: str, history_text: str = "") -> bool:
    """
    Cheap, deterministic check for whether a question contains any
    vocabulary plausibly related to the ESG dataset.

    Returns True if at least one whole word overlaps with the domain
    vocabulary (matching on word stems via simple suffix stripping,
    e.g. "emissions" still matches "emission"). Returns False for
    messages with no overlap at all — greetings, small talk, and
    clearly unrelated topics.

    This is deliberately permissive: it is meant to catch obvious
    off-topic input, not to be a precise classifier. Ambiguous or
    borderline cases are left to the LLM intent classifier.
    """

    tokens = {t.lower() for t in _WORD_RE.findall(f"{question} {history_text}")}

    if not tokens:
        return False

    for token in tokens:

        if len(token) < 3:
            # Too short for a safe stem/substring comparison (e.g.
            # "are", "top" as a fragment of other words) — only exact
            # match counts.
            if token in _DOMAIN_VOCABULARY:
                return True
            continue

        for vocab_word in _DOMAIN_VOCABULARY:

            if len(vocab_word) < 4:
                # Short vocab words (e.g. "top", "esg") only match
                # whole tokens, not as substrings of longer words.
                if token == vocab_word:
                    return True
                continue

            # Simple stem match: one is a prefix of the other, with
            # both sides at least 4 characters to avoid accidental
            # short-fragment collisions ("are" inside "average",
            # "rain" inside "training").
            shorter, longer = sorted((token, vocab_word), key=len)
            if len(shorter) >= 4 and longer.startswith(shorter):
                return True

    return False