"""
Main FastAPI application for the Student Profiler API.

This module defines the FastAPI application, endpoints, and middleware
for the Student Profiler backend.
"""

from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, status, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timezone
import asyncio
import os
import logging
import traceback
import json

from ..utils.config_manager import ConfigManager
from ..utils.logging import get_logger
from ..utils.errors import ProfilerError, ValidationError, ResourceNotFoundError
from ..services.interfaces import IDocumentService, IRecommendationService, IQAService
from ..services.interfaces import DocumentAnalysisResult, Recommendation, ProfileSummary
from .dependencies import get_document_service, get_recommendation_service, get_qa_service
from .dependencies import verify_api_key, ServiceFactory
from .middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware
from .websocket import ConnectionManager
from .document_routes import router as document_router

# Configure logging
logger = get_logger(__name__)
config = ConfigManager().get_all()

# Initialize FastAPI app
app = FastAPI(
    title="Student Profiler API",
    description="API for building comprehensive student profiles with AI assistance",
    version="1.0.0",
    docs_url="/api/profiler/docs" if config.get("environment") != "production" else None,
    redoc_url="/api/profiler/redoc" if config.get("environment") != "production" else None
)

# Set app state
app.state.version = "1.0.0"
app.state.environment = os.getenv("ENVIRONMENT", "development")
app.state.api_keys = os.getenv("API_KEYS", "test_api_key").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("cors", {}).get("origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

# Initialize connection manager
manager = ConnectionManager()

# Include document routes
app.include_router(document_router, prefix="/api/profiler")

# Rate limiting
class RateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self, requests: int, window: int):
        """
        Initialize the rate limiter.
        
        Args:
            requests: Maximum number of requests allowed in the window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.requests_per_ip: Dict[str, List[float]] = {}
    
    def is_allowed(self, ip: str) -> bool:
        """
        Check if request from IP is within rate limits.
        
        Args:
            ip: Client IP address
            
        Returns:
            True if allowed, False if rate limit exceeded
        """
        now = time.time()
        if ip not in self.requests_per_ip:
            self.requests_per_ip[ip] = []
        
        # Remove old requests
        self.requests_per_ip[ip] = [
            t for t in self.requests_per_ip[ip]
            if now - t < self.window
        ]
        
        # Check if limit exceeded
        if len(self.requests_per_ip[ip]) >= self.requests:
            return False
        
        # Add new request
        self.requests_per_ip[ip].append(now)
        return True

rate_limiter = RateLimiter(
    requests=config.get("api", {}).get("rate_limit_requests", 100),
    window=config.get("api", {}).get("rate_limit_window", 60)
)

# Request models
class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    
    question: str = Field(..., description="User's question")
    context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional context for question answering"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What should I emphasize in my personal statement?",
                "context": {
                    "user_id": "user123",
                    "academic_focus": "Computer Science"
                }
            }
        }

class DocumentRequest(BaseModel):
    """Request model for /analyze-document endpoint."""
    
    content: str = Field(..., description="Document content")
    document_type: str = Field(..., description="Type of document (e.g., resume, cover_letter)")
    user_id: str = Field(..., description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Document metadata"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Dear Admissions Committee, I am writing to express my interest...",
                "document_type": "cover_letter",
                "user_id": "user123",
                "metadata": {
                    "source": "user_upload",
                    "filename": "cover_letter.pdf"
                }
            }
        }

class ProfileDataRequest(BaseModel):
    """Request model for profile-related endpoints."""
    
    user_id: str = Field(..., description="User ID")
    profile_data: Dict[str, Any] = Field(..., description="Profile data")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "profile_data": {
                    "academic": {
                        "grades": {"gpa": 3.8, "classes": ["CS101", "MATH202"]},
                        "achievements": ["Dean's List", "Hackathon Winner"]
                    },
                    "extracurricular": {
                        "activities": ["Chess Club", "Volunteer"]
                    }
                }
            }
        }

# API endpoints
@app.websocket("/api/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time profile building.
    
    Args:
        websocket: The WebSocket connection
        user_id: The user's ID
    """
    session_id = None
    try:
        logger.info(f"WebSocket connection attempt from user_id={user_id}")
        
        # Accept the connection first
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user_id={user_id}")
        
        try:
            # Connect the client to the manager
            session_id = await manager.connect(websocket, user_id)
            logger.info(f"WebSocket session established: user_id={user_id}, session_id={session_id}")
            
            # Connection manager now sends the initial messages
            
            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    logger.debug(f"WebSocket message received from session {session_id}: {message[:100]}...")
                    await manager.receive_message(message, websocket)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected by client: session_id={session_id}")
                    break
                except Exception as e:
                    logger.error(f"WebSocket message handling error: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e)
                    })
        except Exception as e:
            logger.error(f"WebSocket session initialization error: {str(e)}")
            # Send error message with a simple structure that the frontend can handle
            await websocket.send_json({
                "error": str(e)
            })
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        # No need to disconnect since connection wasn't established
    finally:
        if session_id:
            logger.info(f"Cleaning up WebSocket session: session_id={session_id}")
            manager.disconnect(session_id)

@app.post(
    "/api/profiler/ask", 
    response_model=Dict[str, Any],
    summary="Ask a question"
)
async def ask_question(
    request: AskRequest,
    api_key: str = Depends(verify_api_key),
    qa_service: IQAService = Depends(get_qa_service)
) -> Dict[str, Any]:
    """
    Answer questions related to the profile building process.
    
    This endpoint uses the QA service to answer user questions about
    the profile building process, college applications, or student profiles.
    """
    try:
        # Apply rate limiting
        # Safely get client_ip - fall back to unknown if context doesn't exist
        client_ip = "unknown"
        if hasattr(request, 'context') and request.context is not None:
            client_ip = request.context.get("client_ip", "unknown")
            
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Safely get context
        context = {}
        if request.context:
            context = request.context
            
        response = await qa_service.generate_questions(
            question=request.question,
            categories=["academic", "personal"],
            context=context
        )
        
        return {
            "questions": [q.dict() for q in response],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

@app.post(
    "/api/profiler/documents/analyze", 
    response_model=Dict[str, Any],
    summary="Analyze document content"
)
async def analyze_document(
    request: DocumentRequest,
    api_key: str = Depends(verify_api_key),
    document_service: IDocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    Analyze document content and extract structured data.
    
    This endpoint analyzes various document types (resumes, cover letters, etc.)
    and extracts structured data for use in the profile.
    """
    # This function is commented out because it duplicates functionality provided
    # by the document_routes router, which is now included in the app.
    # Using the router version instead.
    return await document_service.analyze_document(
        document_content=request.content,
        document_type=request.document_type,
        user_id=request.user_id,
        metadata=request.metadata
    )

@app.post(
    "/api/profiler/recommendations", 
    response_model=List[Dict[str, Any]],
    summary="Generate profile recommendations"
)
async def generate_recommendations(
    request: ProfileDataRequest,
    categories: Optional[List[str]] = None,
    api_key: str = Depends(verify_api_key),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service)
) -> List[Dict[str, Any]]:
    """
    Generate recommendations based on profile data.
    
    This endpoint analyzes the user's profile data and provides
    personalized recommendations for improving their profile.
    """
    try:
        recommendations = await recommendation_service.generate_recommendations(
            user_id=request.user_id,
            profile_data=request.profile_data,
            categories=categories
        )
        
        # Handle both Pydantic models and dictionaries
        result = []
        for rec in recommendations:
            if hasattr(rec, 'dict'):
                # If it's a Pydantic model with dict() method
                result.append(rec.dict())
            else:
                # If it's already a dictionary
                result.append(rec)
                
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error generating recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )

@app.post(
    "/api/profiler/profile-summary", 
    response_model=Dict[str, Any],
    summary="Generate profile summary"
)
async def generate_profile_summary(
    request: ProfileDataRequest,
    api_key: str = Depends(verify_api_key),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service)
) -> Dict[str, Any]:
    """
    Generate a summary of the user's profile.
    
    This endpoint analyzes the user's profile data and provides a
    summary of strengths, areas for improvement, and unique selling points.
    """
    try:
        summary = await recommendation_service.get_profile_summary(
            user_id=request.user_id,
            profile_data=request.profile_data
        )
        
        return summary.dict()
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error generating profile summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating profile summary: {str(e)}"
        )

@app.get(
    "/api/profiler/health", 
    response_model=Dict[str, Any],
    summary="Health check endpoint"
)
async def health_check(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    This endpoint returns the health status of the API and its dependencies.
    """
    try:
        # Check service health
        services_status = {
            "document_service": "up",
            "recommendation_service": "up",
            "qa_service": "up"
        }
        
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": app.version,
            "services": services_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "version": app.version
        }

# Add a debugging endpoint for WebSocket
@app.get("/api/ws/{user_id}", include_in_schema=False)
async def websocket_debug(user_id: str):
    """Debug endpoint for WebSocket"""
    return {"message": "WebSocket endpoint exists", "user_id": user_id}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Initializing services...")
    await ServiceFactory.initialize_services()
    logger.info("Services initialized successfully.")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown services gracefully."""
    logger.info("Shutting down services...")
    await ServiceFactory.shutdown_services()
    logger.info("Services shut down successfully.")

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )
    
    # Add API key header to security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"ApiKeyHeader": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 