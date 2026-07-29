from langchain_core.prompts import ChatPromptTemplate

INTENT_PROMPT = ChatPromptTemplate.from_template("""
You are an intent classification assistant.

Your job is to classify a user's request into ONE category.

Categories:

READ
- Questions asking to retrieve, summarize, aggregate, compare, count, filter, analyze or visualize existing data.

WRITE
- Any request that modifies the database.
- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- CREATE
- TRUNCATE
- REPLACE
- MERGE
- PRAGMA
- ATTACH
- DETACH
- Any request asking to change, remove, edit or create data.

Rules:

Return ONLY one word.

READ

or

WRITE

Question:
{question}
""")


SQL_GENERATION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert SQLite SQL developer.

Generate exactly ONE SQLite SELECT statement.

Database Schema:

{schema}

User Question:

{question}

Rules:

1. Return ONLY SQL.
2. Do NOT explain anything.
3. Do NOT use markdown.
4. Do NOT wrap SQL inside ``` blocks.
5. Generate exactly one SELECT statement.
6. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE, MERGE, PRAGMA, ATTACH or DETACH.
7. Use only tables and columns present in the schema.
8. Prefer explicit column names instead of SELECT *.
9. Use LIMIT when the user asks for sample, first, top or example records.
10. If aggregation is required, use appropriate GROUP BY.
11. If sorting is requested, use ORDER BY.
12. If the question cannot be answered from the schema, return exactly:

UNSUPPORTED_QUERY
""")

INSIGHT_PROMPT = ChatPromptTemplate.from_template("""
You are an ESG Analytics Assistant.

Generate a concise executive summary.

User Question

{question}

Query Summary

{summary}

Rules

Use only the supplied information.

Do not invent facts.

Mention

• Highest values

• Lowest values

• Trends if visible

• Significant comparisons

Keep the response between 3 and 6 sentences.

Write for business executives.

Avoid SQL terminology.
""")
