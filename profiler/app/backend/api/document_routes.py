"""
Document API endpoints.

This module provides the FastAPI routes for the document service.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field

from ..services.document_service import DocumentService, DocumentType, DocumentAnalysis
from ..services.document_service.models import AnalysisInsight
from .dependencies import get_document_service, verify_api_key

# Create router
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(verify_api_key)]
)

class DocumentRequest(BaseModel):
    """Request model for document analysis"""
    content: str = Field(..., description="Document content")
    document_type: Optional[str] = Field(None, description="Document type (transcript, essay, resume, letter)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class DocumentResponse(BaseModel):
    """Response model for document analysis"""
    content_type: str = Field(..., description="Document type")
    extracted_info: Dict[str, Any] = Field(..., description="Extracted information")
    insights: List[AnalysisInsight] = Field(default_factory=list, description="Analysis insights")
    confidence: float = Field(..., description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="Document type detected or provided")
    status: str = Field("success", description="Upload status")

@router.post("/analyze", response_model=DocumentResponse)
async def analyze_document(
    request: DocumentRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Analyze a document and extract information.
    
    Args:
        request: Document analysis request
        
    Returns:
        Analysis results
    """
    try:
        # Determine document type
        if request.document_type:
            try:
                document_type = DocumentType(request.document_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid document type: {request.document_type}"
                )
        else:
            document_type = await document_service.detect_document_type(request.content)
        
        # Validate content is not empty
        if not request.content:
            raise HTTPException(
                status_code=422,
                detail="Document content cannot be empty"
            )
            
        # Analyze document
        result = await document_service.analyze(
            content=request.content,
            document_type=document_type,
            metadata=request.metadata
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        if "Document content cannot be empty" in str(e) or "Invalid document type" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload and analyze a document.
    
    Args:
        file: Document file
        document_type: Optional document type
        section: Optional profile section this document belongs to
        
    Returns:
        Document upload result with document ID
    """
    try:
        # Read file content
        content = await file.read()
        
        # Convert content to string
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        
        # Create metadata from file info
        meta_dict = {
            "filename": file.filename,
            "content_type": file.content_type,
            "section": section or "general"
        }
        
        # Determine document type
        if document_type:
            try:
                doc_type = DocumentType(document_type.lower())
            except ValueError:
                doc_type = await document_service.detect_document_type(content)
        else:
            doc_type = await document_service.detect_document_type(content)
        
        # Store document and get ID
        document_id = await document_service.store_document(
            content=content,
            document_type=doc_type,
            metadata=meta_dict
        )
        
        # Start analysis in background (don't wait for it)
        import asyncio
        asyncio.create_task(document_service.analyze(
            content=content,
            document_type=doc_type,
            metadata=meta_dict
        ))
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            content_type=doc_type.value,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=List[Dict[str, str]])
async def get_document_types():
    """
    Get a list of supported document types.
    
    Returns:
        List of document types with descriptions
    """
    return [
        {"value": DocumentType.TRANSCRIPT.value, "description": "Academic transcript"},
        {"value": DocumentType.ESSAY.value, "description": "Essay or paper"},
        {"value": DocumentType.RESUME.value, "description": "Resume or CV"},
        {"value": DocumentType.LETTER.value, "description": "Letter"},
        {"value": DocumentType.OTHER.value, "description": "Other document type"}
    ] 