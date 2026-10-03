# api/main.py

from pathlib import Path
import json
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


# ============================================================
# PROJECT IMPORTS
# ============================================================

from src.retrieval.retriever import ArchitectureRetriever
from src.generation.answer_generator import (
    ArchitectureAnswerGenerator
)
from src.comparison.revision_compare import (
    RevisionComparator
)

from database.database import (
    ArchitectureDatabase
)


# ============================================================
# FILE PATHS
# ============================================================

ARCHITECTURE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "extracted_entities"
    / "architecture_knowledge.json"
)

RAG_INDEX_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "rag_index"
    / "autosar_hld.faiss"
)

RAG_DOCUMENTS_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "rag_index"
    / "rag_documents.json"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AUTOSAR HLD Analysis Assistant API",
    description=(
        "Backend API for AUTOSAR HLD architecture "
        "analysis, evidence-grounded search and "
        "revision comparison."
    ),
    version="1.0.0"
)


# ============================================================
# DATABASE
# ============================================================

database = ArchitectureDatabase()


# ============================================================
# LOAD ARCHITECTURE
# ============================================================

def load_architecture():

    if not ARCHITECTURE_FILE.exists():

        raise FileNotFoundError(
            "Architecture knowledge file not found: "
            f"{ARCHITECTURE_FILE}"
        )

    with open(
        ARCHITECTURE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# LOAD RAG SYSTEM
# ============================================================

def load_rag_system():

    if not RAG_INDEX_FILE.exists():

        raise FileNotFoundError(
            f"FAISS index not found: "
            f"{RAG_INDEX_FILE}"
        )

    if not RAG_DOCUMENTS_FILE.exists():

        raise FileNotFoundError(
            f"RAG documents not found: "
            f"{RAG_DOCUMENTS_FILE}"
        )

    retriever = ArchitectureRetriever()

    retriever.load_index(
        RAG_INDEX_FILE,
        RAG_DOCUMENTS_FILE
    )

    generator = ArchitectureAnswerGenerator()

    return retriever, generator


# ============================================================
# REQUEST MODELS
# ============================================================

class QueryRequest(BaseModel):

    question: str

    top_k: int = 5


class ComparisonRequest(BaseModel):

    old_architecture: dict

    new_architecture: dict

    old_document: Optional[str] = None

    new_document: Optional[str] = None


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health"
)
def health():

    architecture_available = (
        ARCHITECTURE_FILE.exists()
    )

    rag_index_available = (
        RAG_INDEX_FILE.exists()
    )

    rag_documents_available = (
        RAG_DOCUMENTS_FILE.exists()
    )

    database_available = (
        database.health_check()
    )

    return {
        "status": "healthy",
        "service": (
            "AUTOSAR HLD Analysis Assistant API"
        ),
        "architecture_available":
            architecture_available,
        "rag_index_available":
            rag_index_available,
        "rag_documents_available":
            rag_documents_available,
        "database_available":
            database_available
    }


# ============================================================
# ARCHITECTURE
# ============================================================

@app.get(
    "/architecture"
)
def get_architecture():

    try:

        architecture = load_architecture()

        return {
            "status": "success",
            "architecture": architecture
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# QUERY
# ============================================================

@app.post(
    "/query"
)
def query_architecture(
    request: QueryRequest
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    if request.top_k < 1:

        raise HTTPException(
            status_code=400,
            detail="top_k must be at least 1."
        )

    try:

        retriever, generator = (
            load_rag_system()
        )

        retrieved_results = (
            retriever.hybrid_search(
                question,
                top_k=request.top_k
            )
        )

        result = generator.generate(
            question,
            retrieved_results
        )

        answer = result.get(
            "answer",
            ""
        )

        evidence = result.get(
            "evidence",
            []
        )

        citation_count = sum(
            "Citation:" in line
            for line in answer.splitlines()
        )

        query_id = database.add_query(
            question=question,
            intent=result.get(
                "intent",
                "general"
            ),
            answer=answer,
            evidence_count=len(evidence),
            citation_count=citation_count
        )

        return {
            "status": "success",
            "query_id": query_id,
            "query": question,
            "intent": result.get(
                "intent",
                "general"
            ),
            "answer": answer,
            "evidence_count": len(
                evidence
            ),
            "citation_count":
                citation_count,
            "evidence":
                evidence
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# REVISION COMPARISON
# ============================================================

@app.post(
    "/compare"
)
def compare_architecture(
    request: ComparisonRequest
):

    try:

        comparator = RevisionComparator(
            request.old_architecture,
            request.new_architecture
        )

        comparison = (
            comparator.compare()
        )

        comparison_id = (
            database.add_comparison(
                old_document=(
                    request.old_document
                    or "previous_revision"
                ),
                new_document=(
                    request.new_document
                    or "new_revision"
                ),
                comparison=comparison
            )
        )

        return {
            "status": "success",
            "comparison_id":
                comparison_id,
            "comparison":
                comparison
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# QUERY HISTORY
# ============================================================

@app.get(
    "/query-history"
)
def query_history(
    limit: int = 50
):

    if limit < 1:

        raise HTTPException(
            status_code=400,
            detail="limit must be at least 1."
        )

    return {
        "status": "success",
        "count": len(
            database.get_query_history(
                limit
            )
        ),
        "queries":
            database.get_query_history(
                limit
            )
    }


# ============================================================
# COMPARISON HISTORY
# ============================================================

@app.get(
    "/comparison-history"
)
def comparison_history(
    limit: int = 50
):

    if limit < 1:

        raise HTTPException(
            status_code=400,
            detail="limit must be at least 1."
        )

    return {
        "status": "success",
        "count": len(
            database.get_comparison_history(
                limit
            )
        ),
        "comparisons":
            database.get_comparison_history(
                limit
            )
    }


# ============================================================
# DOCUMENTS
# ============================================================

@app.get(
    "/documents"
)
def documents():

    records = database.get_documents()

    return {
        "status": "success",
        "count": len(records),
        "documents": records
    }


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/"
)
def root():

    return {
        "service":
            "AUTOSAR HLD Analysis Assistant API",
        "version":
            "1.0.0",
        "documentation":
            "/docs",
        "health":
            "/health"
    }