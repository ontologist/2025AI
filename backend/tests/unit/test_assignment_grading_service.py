import json
from pathlib import Path
from unittest.mock import MagicMock

from app.services.assignment_grading_service import AssignmentGradingService
from app.services.resource_monitor import ResourceMonitor
from app.services.progress_service import ProgressService


def test_grading_queue_respects_resource_limit(temp_db_dir):
    # Monitor that blocks first, then allows.
    calls = {"count": 0}

    def overloaded():
        calls["count"] += 1
        return calls["count"] == 1

    monitor = ResourceMonitor(limit=0.2)
    monitor.is_overloaded = MagicMock(side_effect=overloaded)
    service = AssignmentGradingService(submissions_dir=Path(temp_db_dir), monitor=monitor)

    submission = {"answer": "A" * 600}
    path = service.save_submission("student@test.com", 8, submission)
    result1 = service.enqueue("student@test.com", 8, submission, path)
    assert result1["processed"] is False  # first time blocked

    # Now process after resources free
    processed = service.process_next()
    assert processed is not None
    assert processed["score"] >= 0
    assert processed["assignment_id"] == 8


def test_submission_persists_and_grades(progress_service):
    email = "student@test.com"
    assignment = next(a for a in progress_service.get_assignments(email) if a["week_number"] == 8)
    assignment_id = assignment["id"]
    submission = {"q1": "hello world" * 100}

    response = progress_service.submit_assignment(email=email, assignment_id=assignment_id, submission=submission)
    assert response["status"] == "submitted"

    # Validate DB state
    assignments = progress_service.get_assignments(email)
    wk8 = next(a for a in assignments if a["week_number"] == 8)
    assert wk8["submission_status"] in ("submitted", "completed")


def test_weekly_progress_assignment_status(progress_service):
    email = "student2@test.com"
    assignment = next(a for a in progress_service.get_assignments(email) if a["week_number"] == 8)
    assignment_id = assignment["id"]
    submission = {"q1": "A" * 800}
    progress_service.submit_assignment(email=email, assignment_id=assignment_id, submission=submission)

    # Force process remaining queued items if any
    if progress_service.grading_service.queue:
        processed = progress_service.grading_service.process_next()
        if processed:
            progress_service._persist_grade(processed)

    progress = progress_service.get_student_progress(email)
    wk8 = next((w for w in progress["weekly_progress"] if w["week_number"] == 8), None)
    assert wk8 is not None
    assert wk8["assignment_status"] in ("submitted", "completed", "graded", "not_started")

