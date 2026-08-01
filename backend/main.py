from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
