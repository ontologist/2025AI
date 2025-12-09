"""Progress tracking API endpoints."""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from app.services.progress_service import ProgressService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize progress service
progress_service = ProgressService()


class PageViewRequest(BaseModel):
    """Request model for recording a page view."""
    email: str
    page_path: str
    page_title: str = ""
    time_spent: int = 0


class BotInteractionRequest(BaseModel):
    """Request model for recording a bot interaction."""
    email: str
    question: str
    response: str
    language: str = "ja"
    topic: Optional[str] = None


class AssignmentSubmitRequest(BaseModel):
    """Request model for submitting an assignment."""
    email: str
    assignment_id: int
    status: str = "submitted"


class SyncRequest(BaseModel):
    """Request model for syncing progress."""
    email: str
    local_data: Dict[str, Any] = {}


class ProgressResponse(BaseModel):
    """Response model for progress data."""
    email: str
    content: Dict[str, Any]
    bot_interactions: Dict[str, Any]
    assignments: Dict[str, Any]
    quizzes: Dict[str, Any]
    weekly_progress: List[Dict[str, Any]]


@router.get("/progress/{email}")
async def get_progress(email: str):
    """
    Get student progress.
    
    Returns comprehensive progress data including content views,
    bot interactions, assignments, and quizzes.
    """
    try:
        progress = progress_service.get_student_progress(email)
        return progress
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting progress: {str(e)}")


@router.post("/progress/page-view")
async def record_page_view(request: PageViewRequest):
    """Record a page view for tracking content progress."""
    try:
        # Ensure student exists
        progress_service.get_or_create_student(request.email)
        
        result = progress_service.record_page_view(
            email=request.email,
            page_path=request.page_path,
            page_title=request.page_title,
            time_spent=request.time_spent
        )
        return result
    except Exception as e:
        logger.error(f"Error recording page view: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recording page view: {str(e)}")


@router.post("/progress/bot-interaction")
async def record_bot_interaction(request: BotInteractionRequest):
    """Record a bot interaction for tracking engagement."""
    try:
        result = progress_service.record_bot_interaction(
            email=request.email,
            question=request.question,
            response=request.response,
            language=request.language,
            topic=request.topic
        )
        return result
    except Exception as e:
        logger.error(f"Error recording bot interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/progress/{email}/viewed-pages")
async def get_viewed_pages(email: str):
    """Get list of pages viewed by student."""
    try:
        pages = progress_service.get_viewed_pages(email)
        return {"email": email, "viewed_pages": pages}
    except Exception as e:
        logger.error(f"Error getting viewed pages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/progress/{email}/assignments")
async def get_assignments(email: str):
    """Get all assignments with student's submission status."""
    try:
        assignments = progress_service.get_assignments(email)
        return {"email": email, "assignments": assignments}
    except Exception as e:
        logger.error(f"Error getting assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/progress/assignment/submit")
async def submit_assignment(request: AssignmentSubmitRequest):
    """Submit or update an assignment."""
    try:
        result = progress_service.submit_assignment(
            email=request.email,
            assignment_id=request.assignment_id,
            status=request.status
        )
        return result
    except Exception as e:
        logger.error(f"Error submitting assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/progress/sync")
async def sync_progress(request: SyncRequest):
    """
    Sync local browser progress with server.
    
    Merges local data with server data, returning the combined result.
    """
    try:
        # Ensure student exists
        progress_service.get_or_create_student(request.email)
        
        result = progress_service.sync_progress(
            email=request.email,
            local_data=request.local_data
        )
        return result
    except Exception as e:
        logger.error(f"Error syncing progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error syncing: {str(e)}")

