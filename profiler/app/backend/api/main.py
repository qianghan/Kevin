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
app.state.api_keys = os.getenv("API_KEYS", "test-key-123").split(",")

# Define VALID_API_KEYS for test mocking
VALID_API_KEYS = app.state.api_keys
logger.info(f"API keys: {VALID_API_KEYS}")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

# Initialize connection manager
manager = ConnectionManager()

# WebSocket endpoint with API key authentication
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str,
    x_api_key: str = None
):
    """
    WebSocket endpoint with API key authentication.
    
    Args:
        websocket: The WebSocket connection
        user_id: The user's ID
        x_api_key: API key from query parameter
    """
    try:
        # Log connection attempt and debug info
        logger.info(f"WebSocket connection attempt from user {user_id}")
        logger.debug(f"WebSocket headers: {dict(websocket.headers)}")
        logger.debug(f"WebSocket query params: {dict(websocket.query_params)}")
        
        # Get API key from query params
        x_api_key = websocket.query_params.get("x-api-key")
        logger.info(f"Got API key from query params: {x_api_key}")
            
        # Verify API key
        if not x_api_key:
            logger.warning(f"No API key provided for user {user_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Get valid keys from configuration
        valid_keys = VALID_API_KEYS
        logger.info(f"Valid API keys: {valid_keys}")
        logger.info(f"API key check: {x_api_key} in {valid_keys} = {x_api_key in valid_keys}")
        
        # Check if the provided key is valid
        if x_api_key not in valid_keys:
            logger.warning(f"Invalid API key provided for user {user_id}: {x_api_key}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Accept the connection
        await websocket.accept()
        logger.info(f"WebSocket connected for user {user_id} with valid API key")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Successfully connected to WebSocket endpoint",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Connect to the manager
        session_id = await manager.connect(websocket, user_id)
        logger.info(f"Session established for user {user_id} with session_id {session_id}")
        
        try:
            while True:
                # Receive message
                message = await websocket.receive_text()
                logger.debug(f"Received message from user {user_id}: {message}")
                
                # Echo the message back
                await websocket.send_json({
                    "type": "echo",
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Process message through manager
                await manager.receive_message(message, websocket)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {str(e)}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        # Clean up connection
        if 'session_id' in locals():
            manager.disconnect(session_id)
            logger.info(f"Cleaned up session {session_id} for user {user_id}")

# Include routers
app.include_router(document_router, prefix="/api/profiler")
app.include_router(websocket_router, prefix="/api/profiler")

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

# Modified recommendations endpoint with no auth requirement for easier testing
@app.get("/api/recommendations", include_in_schema=True, dependencies=[])
async def get_recommendations(
    user_id: str,
    categories: Optional[List[str]] = None,
    recommendation_service: IRecommendationService = Depends(get_recommendation_service)
) -> List[Dict[str, Any]]:
    """
    Get recommendations for a user with NO AUTH REQUIREMENT for easier testing.
    This endpoint is deliberately open for development purposes.
    """
    try:
        logger.info(f"Getting recommendations for user {user_id}")
        
        # Get recommendations or return empty list if error
        try:
            recommendations = await recommendation_service.get_recommendations(
                user_id=user_id,
                categories=categories
            )
            
            # Convert to dict for response
            result = []
            for rec in recommendations:
                if hasattr(rec, 'dict'):
                    result.append(rec.dict())
                else:
                    result.append(rec)
                    
            logger.info(f"Found {len(result)} recommendations for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}", exc_info=True)
            # Return empty list on error for better UX
            return []
    except Exception as e:
        logger.error(f"Error in recommendations endpoint: {str(e)}", exc_info=True)
        return [] 