from fastapi import FastAPI
from app.database import init_db
from app.api import operators_router, sources_router, requests_router

app = FastAPI(
    title="Mini CRM - Lead Distribution System",
    description="A service for distributing leads among operators based on source weights and load limits",
    version="1.0.0"
)

app.include_router(operators_router)
app.include_router(sources_router)
app.include_router(requests_router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Mini CRM - Lead Distribution System",
        "docs": "/docs",
        "endpoints": {
            "operators": "/operators",
            "sources": "/sources",
            "requests": "/requests"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
