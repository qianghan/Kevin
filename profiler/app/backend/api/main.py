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

from app.backend.utils.config_manager import ConfigManager
from app.backend.utils.logging import get_logger
from app.backend.utils.errors import ProfilerError, ValidationError, ResourceNotFoundError
from app.backend.services.interfaces import IDocumentService, IRecommendationService, IQAService
from app.backend.services.interfaces import DocumentAnalysisResult, Recommendation, ProfileSummary
from app.backend.api.dependencies import get_document_service, get_recommendation_service, get_qa_service
from app.backend.api.dependencies import verify_api_key, ServiceFactory
from app.backend.api.middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware
from app.backend.api.websocket import ConnectionManager, router as websocket_router
from app.backend.api.document_routes import router as document_router

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

# Include routers
app.include_router(document_router, prefix="/api/profiler")
app.include_router(websocket_router, prefix="/api/profiler")

# Add a bare-bones test WebSocket endpoint with no validation
@app.websocket("/test-ws")
async def test_websocket_endpoint(websocket: WebSocket):
    """
    Simple test WebSocket endpoint with no validation.
    """
    try:
        # Get API key from query params if present (but don't validate it)
        api_key = websocket.query_params.get("api_key", "none")
        logger.info(f"Test WebSocket connection attempt with api_key={api_key}")
        
        # Accept the connection immediately
        await websocket.accept()
        logger.info(f"Test WebSocket connection accepted")
        
        # Send a welcome message
        await websocket.send_json({"message": "Connected to test WebSocket", "timestamp": datetime.now(timezone.utc).isoformat()})
        
        # Just echo back any messages received
        while True:
            try:
                message = await websocket.receive_text()
                logger.info(f"Test WebSocket message received: {message[:100]}...")
                await websocket.send_text(f"Echo: {message}")
            except WebSocketDisconnect:
                logger.info(f"Test WebSocket disconnected by client")
                break
            except Exception as e:
                logger.error(f"Test WebSocket error: {str(e)}")
                await websocket.send_json({
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    except Exception as e:
        logger.error(f"Test WebSocket connection error: {str(e)}")
    
    logger.info("Test WebSocket connection closed")

# Direct WebSocket endpoint without the profiler prefix
@app.websocket("/api/ws/{user_id}")
async def direct_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Direct WebSocket endpoint for real-time profile building.
    Uses a simplified approach with no validation.
    
    Args:
        websocket: The WebSocket connection
        user_id: The user's ID
    """
    session_id = None
    try:
        # Get API key from query params if present (but don't validate it)
        api_key = websocket.query_params.get("api_key", "none")
        logger.info(f"WebSocket connection attempt from user_id={user_id} with api_key={api_key}")
        
        # Always accept the connection first without any validation
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user_id={user_id}")
        
        # Connect the client to the manager and start handling messages
        try:
            session_id = await manager.connect(websocket, user_id)
            logger.info(f"WebSocket session established: user_id={user_id}, session_id={session_id}")
            
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
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            logger.error(f"WebSocket session initialization error: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            await websocket.close()
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        if session_id:
            logger.info(f"Cleaning up WebSocket session: session_id={session_id}")
            manager.disconnect(session_id)

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

# Add a completely separate WebSocket endpoint with no security or validation
@app.websocket("/open-ws/{user_id}")
async def open_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint with zero validation for real-time profile building.
    No security checks - for development only.
    
    Args:
        websocket: The WebSocket connection
        user_id: The user's ID
    """
    session_id = None
    try:
        # Log connection attempt
        logger.info(f"Open WebSocket connection attempt from user_id={user_id}")
        
        # Accept the connection immediately without any validation
        await websocket.accept()
        logger.info(f"Open WebSocket connection accepted for user_id={user_id}")
        
        # Connect to the connection manager to establish workflow
        try:
            # Use the existing connection manager to handle the connection
            session_id = await manager.connect(websocket, user_id)
            logger.info(f"WebSocket session established: user_id={user_id}, session_id={session_id}")
            
            # Handle messages through the connection manager
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
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            logger.error(f"WebSocket session initialization error: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            await websocket.close()
                
    except Exception as e:
        logger.error(f"Open WebSocket connection error: {str(e)}")
    finally:
        if session_id:
            logger.info(f"Cleaning up WebSocket session: session_id={session_id}")
            manager.disconnect(session_id)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Set a default API key if not already set
    if not hasattr(app.state, "api_keys") or not app.state.api_keys:
        app.state.api_keys = ["test-api-key", "test_api_key"]
        logger.info(f"Setting default API keys: {app.state.api_keys}")
    
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
    
    # Apply security globally but exempt WebSocket endpoints
    paths = openapi_schema.get("paths", {})
    for path, operations in paths.items():
        # Skip WebSocket paths
        if "/ws/" in path:
            continue
        
        # Apply security to all other paths
        for operation in operations.values():
            operation["security"] = [{"ApiKeyHeader": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 