"""Quiz API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from app.services.quiz_service import QuizService
from app.services.roster_service import RosterService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize quiz service
quiz_service = QuizService()
roster_service = RosterService()


class GenerateQuizRequest(BaseModel):
    """Request model for generating a quiz."""
    email: str
    week_number: Optional[int] = None
    topic: Optional[str] = None
    num_questions: int = 5
    difficulty: str = "medium"


class SubmitQuizRequest(BaseModel):
    """Request model for submitting quiz answers."""
    email: str
    quiz_id: int
    answers: Dict[str, str]  # question index -> answer (A, B, C, or D)
    time_taken: int = 0


@router.post("/quiz/generate")
async def generate_quiz(request: GenerateQuizRequest):
    """
    Generate an adaptive quiz for a student.
    
    The quiz adapts based on student's progress and previous performance.
    """
    _ensure_enrolled(request.email)
    try:
        quiz = await quiz_service.generate_quiz(
            email=request.email,
            week_number=request.week_number,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        return quiz
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@router.get("/quiz/topics")
async def get_available_topics():
    """Get list of available quiz topics by week."""
    from app.services.quiz_service import COURSE_TOPICS
    return {"topics": COURSE_TOPICS}


def _ensure_enrolled(email: str):
    if "@" not in email:
        return
    student = roster_service.get_student(email)
    if not student:
        raise HTTPException(status_code=403, detail="Not enrolled")


@router.post("/quiz/submit")
async def submit_quiz(request: SubmitQuizRequest):
    """
    Submit quiz answers and get results.
    
    Returns score, percentage, and detailed results for each question.
    """
    _ensure_enrolled(request.email)
    try:
        # Convert string keys to int for answers
        answers = {int(k): v for k, v in request.answers.items()}
        
        result = await quiz_service.submit_quiz(
            email=request.email,
            quiz_id=request.quiz_id,
            answers=answers,
            time_taken=request.time_taken
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: int):
    """Get a quiz by ID."""
    try:
        quiz = quiz_service.get_quiz(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return quiz
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/quiz/history/{email}")
async def get_quiz_history(email: str):
    """Get quiz attempt history for a student."""
    _ensure_enrolled(email)
    try:
        history = quiz_service.get_quiz_history(email)
        return {"email": email, "history": history}
    except Exception as e:
        logger.error(f"Error getting quiz history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


