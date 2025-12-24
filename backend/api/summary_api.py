from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from typing import Optional, List
from datetime import datetime, timedelta
from backend.auth import get_current_user
from utils.database import (
    get_summary_by_id,
    get_user_summaries_with_pagination,
    get_book_summary_versions,
    update_summary_metadata,
    delete_summary,
    restore_summary,
    set_active_summary_version,
    get_all_summaries_admin,
    get_summary_analytics,
    db
)

router = APIRouter(prefix="/api/summaries", tags=["summaries"])

# ---------- USER ENDPOINTS ----------

@router.get("/")
async def get_user_summaries(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    book_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_word_count: Optional[int] = None,
    max_word_count: Optional[int] = None
):
    """Get user's summaries with pagination and filtering"""
    filters = {}
    if book_id:
        filters["book_id"] = book_id
    if is_active is not None:
        filters["is_active"] = is_active
    if min_word_count:
        filters["min_word_count"] = min_word_count
    if max_word_count:
        filters["max_word_count"] = max_word_count
    
    return get_user_summaries_with_pagination(
        user_id=current_user["_id"],
        page=page,
        limit=limit,
        filters=filters
    )

@router.get("/{summary_id}")
async def get_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific summary"""
    summary = get_summary_by_id(summary_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Check if user owns the summary
    if str(summary["user_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return summary

@router.get("/book/{book_id}/versions")
async def get_summary_versions(
    book_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all summary versions for a book"""
    return get_book_summary_versions(book_id, current_user["_id"])

@router.put("/{summary_id}/metadata")
async def update_summary(
    summary_id: str,
    metadata: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update summary metadata"""
    success = update_summary_metadata(
        summary_id=summary_id,
        user_id=current_user["_id"],
        updates=metadata
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Summary not found or not authorized")
    
    return {"success": True, "message": "Summary metadata updated"}

@router.put("/book/{book_id}/set-active/{version}")
async def set_active_version(
    book_id: str,
    version: int,
    current_user: dict = Depends(get_current_user)
):
    """Set a specific version as active"""
    success = set_active_summary_version(book_id, current_user["_id"], version)
    
    if not success:
        raise HTTPException(status_code=404, detail="Version not found or not authorized")
    
    return {"success": True, "message": f"Version {version} set as active"}

@router.delete("/{summary_id}")
async def delete_user_summary(
    summary_id: str,
    permanent: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """Delete a summary (soft delete by default)"""
    success = delete_summary(summary_id, current_user["_id"], permanent)
    
    if not success:
        raise HTTPException(status_code=404, detail="Summary not found or not authorized")
    
    action = "permanently deleted" if permanent else "soft deleted"
    return {"success": True, "message": f"Summary {action}"}

@router.post("/{summary_id}/restore")
async def restore_user_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Restore a soft-deleted summary"""
    success = restore_summary(summary_id, current_user["_id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Summary not found or cannot be restored")
    
    return {"success": True, "message": "Summary restored"}

# ---------- ADMIN ENDPOINTS ----------

@router.get("/admin/all")
async def get_all_summaries_admin_endpoint(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    book_id: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """Admin: Get all summaries in the system"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if book_id:
        filters["book_id"] = book_id
    if is_active is not None:
        filters["is_active"] = is_active
    
    return get_all_summaries_admin(page=page, limit=limit, filters=filters)

@router.get("/admin/analytics")
async def get_admin_analytics(
    current_user: dict = Depends(get_current_user),
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d|all)$")
):
    """Admin: Get summary analytics"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_summary_analytics(time_range)

@router.delete("/admin/{summary_id}")
async def admin_delete_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user),
    permanent: bool = Query(True)
):
    """Admin: Delete any summary"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get summary to get user_id
    summary = db.summaries.find_one({"_id": ObjectId(summary_id)})
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    success = delete_summary(summary_id, str(summary["user_id"]), permanent)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete summary")
    
    action = "permanently deleted" if permanent else "soft deleted"
    return {"success": True, "message": f"Summary {action} by admin"}