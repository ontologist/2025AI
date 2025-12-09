"""Assignment grading service with simple queue and resource-aware processing."""
from __future__ import annotations

import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Optional, Tuple

from app.core.config import settings
from app.services.resource_monitor import ResourceMonitor


class AssignmentGradingService:
    """Grades assignment submissions sequentially with resource gating."""

    def __init__(self, submissions_dir: Optional[Path] = None, monitor: Optional[ResourceMonitor] = None):
        self.submissions_dir = submissions_dir or Path(__file__).parent.parent.parent / "data" / "assignment_submissions"
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        self.queue: Deque[Dict[str, Any]] = deque()
        self.monitor = monitor or ResourceMonitor()

    def enqueue(self, email: str, assignment_id: int, submission: Dict[str, Any], submission_path: Path) -> Dict[str, Any]:
        """Add a submission to the queue and attempt processing."""
        item = {
            "email": email,
            "assignment_id": assignment_id,
            "submission": submission,
            "submission_path": submission_path,
            "queued_at": datetime.utcnow().isoformat(),
        }
        self.queue.append(item)
        processed = self.process_next()
        return {
            "queued": len(self.queue),
            "processed": processed is not None,
            "result": processed,
        }

    def process_next(self) -> Optional[Dict[str, Any]]:
        """Process the next item if resources allow; otherwise leave it queued."""
        if not self.queue:
            return None
        if self.monitor.is_overloaded():
            return None

        item = self.queue.popleft()
        score, feedback = self._grade(item["submission"])
        graded = {
            "email": item["email"],
            "assignment_id": item["assignment_id"],
            "score": score,
            "feedback": feedback,
            "graded_at": datetime.utcnow().isoformat(),
            "submission_path": str(item["submission_path"]),
        }
        return graded

    def _grade(self, submission: Dict[str, Any]) -> Tuple[int, str]:
        """
        Simple heuristic grading:
        - Count characters across all string fields.
        - Map length to a score up to 100.
        """
        text = json.dumps(submission, ensure_ascii=False)
        length = len(text)
        # 0-500 chars -> up to 60, 500-1500 -> up to 90, >1500 -> 100
        if length <= 0:
            return 0, "No submission content found."
        if length < 500:
            score = int(60 * (length / 500))
        elif length < 1500:
            score = 60 + int(30 * ((length - 500) / 1000))
        else:
            score = 100
        feedback = f"Auto-graded based on submission length ({length} chars)."
        return min(score, 100), feedback

    def save_submission(self, email: str, assignment_id: int, submission: Dict[str, Any]) -> Path:
        """Persist submission JSON to disk and return its path."""
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        user_dir = self.submissions_dir / email.replace("@", "_at_")
        user_dir.mkdir(parents=True, exist_ok=True)
        path = user_dir / f"assignment-{assignment_id}-{ts}.json"
        path.write_text(json.dumps(submission, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

