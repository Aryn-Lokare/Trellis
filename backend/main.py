from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from query_pipeline import build_query_graph

app = FastAPI(
    title="compliance-graphrag-backend",
    description="Backend for the Multi-Modal Knowledge Graph Synthesis for Enterprise Compliance",
    version="0.1.0"
)

# Set up CORS middleware to allow communication with frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class CitationResponse(BaseModel):
    location: str
    source_doc_id: Optional[str] = None
    filename: str
    excerpt: str
    verified: bool

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    status: str

# Instantiate the compiled LangGraph query pipeline
query_graph = build_query_graph()

@app.get("/health")
def health_check():
    """
    Verify backend is running and healthy.
    """
    return {
        "status": "healthy",
        "service": "compliance-graphrag-backend",
        "database": "unverified"
    }

@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    """
    Executes the multi-modal GraphRAG query and retrieval pipeline for a compliance question.
    """
    try:
        initial_state = {
            "question": req.question,
            "question_embedding": None,
            "seed_entity_ids": [],
            "subgraph": {"entities": [], "relationships": []},
            "synthesized_context": "",
            "raw_answer": "",
            "verified_answer": "",
            "citations": [],
            "status": "pending",
            "error_message": None
        }
        
        final_state = query_graph.invoke(initial_state)
        
        return {
            "answer": final_state.get("verified_answer") or final_state.get("raw_answer") or "",
            "citations": final_state.get("citations") or [],
            "status": final_state.get("status") or "success"
        }
    except Exception as e:
        return {
            "answer": f"Error running query pipeline: {str(e)}",
            "citations": [],
            "status": "failed"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
