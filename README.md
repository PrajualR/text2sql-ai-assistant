# ESG Natural Language Analytics

An AI-powered ESG analytics assistant that lets users query manufacturing ESG data using natural language.

## Features

- Natural-language →  SQL generation
- RAG-based ESG knowledge retrieval using ChromaDB
- Conversation-aware follow-up questions
- Automatic insights and visualizations
- Streamlit chat interface

## Architecture

```text
User Question
     ↓
Intent & Topic Validation
     ↓
RAG Retrieval (ChromaDB)
     ↓
SQL Generation (LLM)
     ↓
SQL Validation
     ↓
SQLite Database
     ↓
Insights + Visualization
     ↓
Streamlit
```

## Tech Stack

- Python
- Streamlit
- LangChain
- Groq LLM
- ChromaDB
- BGE embeddings
- SQLite / SQLAlchemy
- SQLGlot
- Pandas
- Plotly

## Live Demo

Try the deployed application:

[ESG Natural Language Analytics](https://text2sql-analytics-assistant.streamlit.app/)
