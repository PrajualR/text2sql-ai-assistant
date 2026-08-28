from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from exceptions import UnsupportedQuestionError
from services.conversation import ConversationContext
from services.sql_service import SQLService


app = FastAPI(
    title="ESG Analytics API",
    description="API layer for the ESG Natural Language Analytics Assistant",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    conversation_id: str


class QueryResponse(BaseModel):
    conversation_id: str
    question: str
    insight: str
    sql: str
    data: list[dict[str, Any]]
    chart_type: str | None = None


# In-memory conversation store for this local/demo application.
# Each React conversation_id maps to the existing ConversationContext.
conversations: dict[str, ConversationContext] = {}


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "ESG Analytics API",
    }


@app.post("/api/conversations")
def create_conversation():
    from uuid import uuid4

    conversation_id = str(uuid4())
    conversations[conversation_id] = ConversationContext()

    return {
        "conversation_id": conversation_id,
    }


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    conversations.pop(conversation_id, None)

    return {
        "status": "ok",
        "conversation_id": conversation_id,
    }


@app.post("/api/query", response_model=QueryResponse)
def process_query(request: QueryRequest):

    conversation = conversations.setdefault(
        request.conversation_id,
        ConversationContext(),
    )

    try:
        result = SQLService.process_question(
            request.question,
            conversation,
        )

    except UnsupportedQuestionError as exc:
        # Unsupported questions are an expected application outcome,
        # not a server error. Return a normal response so the React UI
        # can display the curated user-facing message.
        return QueryResponse(
            conversation_id=request.conversation_id,
            question=request.question,
            insight=str(exc),
            sql="",
            data=[],
            chart_type=None,
        )

    return QueryResponse(
        conversation_id=request.conversation_id,
        question=result.question,
        insight=result.insight,
        sql=result.sql,
        data=result.dataframe.to_dict(orient="records"),
        chart_type=None,
    )