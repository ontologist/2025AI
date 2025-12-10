"""Instructor-facing endpoints for roster upload and reports."""
import io
from typing import List, Dict
from fastapi import APIRouter, UploadFile, HTTPException, File, Form
import pandas as pd
from app.services.roster_service import RosterService
from app.services.progress_service import ProgressService
from app.services.quiz_service import QuizService


router = APIRouter()

roster_service = RosterService()
progress_service = ProgressService()
quiz_service = QuizService()


def _require_instructor(email: str):
    student = roster_service.get_student(email)
    if not student or student.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required")


@router.post("/instructor/roster/upload")
async def upload_roster(file: UploadFile = File(...), instructor_email: str = Form(...)):
    """Upload roster (CSV/XLSX). Only instructors may perform this."""
    _require_instructor(instructor_email)
    try:
        content = await file.read()
        df = roster_service.load_dataframe(file.filename, content)
        summary = roster_service.ingest(df)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest roster: {e}")


@router.get("/instructor/students")
async def list_students(instructor_email: str):
    _require_instructor(instructor_email)
    return roster_service.list_students()


@router.get("/instructor/reports/progress")
async def progress_report(instructor_email: str):
    _require_instructor(instructor_email)
    return roster_service.progress_report(progress_service)


@router.get("/instructor/reports/quizzes")
async def quiz_report(instructor_email: str):
    _require_instructor(instructor_email)
    return roster_service.quiz_report(quiz_service)


@router.get("/instructor/reports/assignments")
async def assignment_report(instructor_email: str):
    _require_instructor(instructor_email)
    return roster_service.assignment_report(progress_service)

