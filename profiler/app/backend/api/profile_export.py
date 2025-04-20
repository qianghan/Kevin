from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime
import json

from ...services.profile.export import ProfileExportService
from ...services.profile.repository import ProfileRepository
from ...models.profile import Profile
from ...models.auth import User
from ...utils.auth import get_current_user

router = APIRouter(prefix="/api/profiler", tags=["profile_export"])

@router.post("/export")
async def export_profile(
    profile_id: str,
    format: str,
    template_id: Optional[str] = None,
    options: Optional[dict] = None,
    current_user: User = Depends(get_current_user)
):
    """Export a profile in the specified format."""
    try:
        # Get profile
        profile_repo = ProfileRepository()
        profile = await profile_repo.get_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        # Check permissions
        if profile.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to export this profile")
            
        # Export profile
        export_service = ProfileExportService()
        filename, content = await export_service.export_profile(
            profile=profile,
            format=format,
            template_id=template_id,
            options=options
        )
        
        # Return file
        return StreamingResponse(
            content,
            media_type=f"application/{format}",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": f"application/{format}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available export templates."""
    try:
        export_service = ProfileExportService()
        templates = await export_service.get_templates()
        return templates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates")
async def create_template(
    template: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new export template."""
    try:
        export_service = ProfileExportService()
        template = await export_service.create_template(template)
        return template
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    template: dict,
    current_user: User = Depends(get_current_user)
):
    """Update an existing export template."""
    try:
        export_service = ProfileExportService()
        template = await export_service.update_template(template_id, template)
        return template
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an export template."""
    try:
        export_service = ProfileExportService()
        await export_service.delete_template(template_id)
        return {"message": "Template deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exports/history")
async def get_export_history(
    current_user: User = Depends(get_current_user)
):
    """Get export history for the current user."""
    try:
        export_service = ProfileExportService()
        history = await export_service.get_export_history()
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 