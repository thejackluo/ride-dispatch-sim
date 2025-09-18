"""
Ride Dispatch Simulator API
Main FastAPI application with CORS configuration for frontend communication
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Ride Dispatch Simulator API",
    description="Backend API for ride-hailing simulation system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    Root endpoint returning API status and basic information

    Returns:
        dict: API status message and version
    """
    return {
        "message": "Ride Dispatch Simulator API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring API availability

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}