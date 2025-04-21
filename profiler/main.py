"""
Main application module.

This module initializes the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from profiler.routers import qa, profile, document, recommendation, notification

app = FastAPI(
    title="Profiler API",
    description="API for the Profiler application",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(qa.router)
app.include_router(profile.router)
app.include_router(document.router)
app.include_router(recommendation.router)
app.include_router(notification.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Profiler API",
        "docs": "/docs",
        "version": "0.1.0",
    } 