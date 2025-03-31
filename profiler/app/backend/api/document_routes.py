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
from .dependencies import get_document_service, validate_api_key

# Create router
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(validate_api_key)]
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
                document_type = await document_service.detect_document_type(request.content)
        else:
            document_type = await document_service.detect_document_type(request.content)
        
        # Analyze document
        result = await document_service.analyze(
            content=request.content,
            document_type=document_type,
            metadata=request.metadata
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload and analyze a document.
    
    Args:
        file: Document file
        document_type: Optional document type
        metadata: Optional metadata (JSON string)
        
    Returns:
        Analysis results
    """
    try:
        # Read file content
        content = await file.read()
        
        # Convert content to string
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        
        # Parse metadata if provided
        meta_dict = {}
        if metadata:
            import json
            try:
                meta_dict = json.loads(metadata)
                
                # Add file info to metadata
                meta_dict["filename"] = file.filename
                meta_dict["content_type"] = file.content_type
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid metadata format. Must be valid JSON."
                )
        else:
            # Just add file info
            meta_dict = {
                "filename": file.filename,
                "content_type": file.content_type
            }
        
        # Determine document type
        if document_type:
            try:
                doc_type = DocumentType(document_type.lower())
            except ValueError:
                doc_type = await document_service.detect_document_type(content)
        else:
            doc_type = await document_service.detect_document_type(content)
        
        # Analyze document
        result = await document_service.analyze(
            content=content,
            document_type=doc_type,
            metadata=meta_dict
        )
        
        return result
        
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