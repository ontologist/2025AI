"""Roster ingestion and instructor reports."""
from __future__ import annotations

import io
import pandas as pd
from typing import Dict, List, Any
from app.models.database import get_db_connection
from app.core.config import settings


class RosterService:
    """Import roster and produce instructor reports."""

    ROLE_MAP = {
        "instructor": "instructor",
        "representative": "instructor",
        "enrolled student": "student",
        "participant": "student",
    }
    EMAIL_DOMAIN = settings.EMAIL_DOMAIN

    def load_dataframe(self, filename: str, content: bytes) -> pd.DataFrame:
        if filename.lower().endswith(".csv"):
            return pd.read_csv(io.BytesIO(content))
        return pd.read_excel(io.BytesIO(content))

    def normalize_role(self, raw: str) -> str:
        if not isinstance(raw, str):
            return "student"
        return self.ROLE_MAP.get(raw.strip().lower(), "student")

    def ingest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Expected columns (case-insensitive match):
        - role (Instructor/Representative/Enrolled Student/Participant)
        - name
        - student_number
        - user_id (left of @)
        """
        cols = {c.lower(): c for c in df.columns}
        role_col = next((c for c in df.columns if "role" in c.lower() or "type" in c.lower()), None)
        name_col = next((c for c in df.columns if "name" in c.lower()), None)
        student_num_col = next((c for c in df.columns if "student" in c.lower() and "number" in c.lower()), None)
        user_col = next((c for c in df.columns if "user" in c.lower() or "id" in c.lower()), None)

        if not role_col or not user_col:
            raise ValueError("Roster must include role/type and user id columns.")

        records = []
        for _, row in df.iterrows():
            user_id = str(row.get(user_col, "")).strip()
            if not user_id:
                continue
            role = self.normalize_role(str(row.get(role_col, "")))
            name = str(row.get(name_col, "")).strip() if name_col else ""
            student_number = str(row.get(student_num_col, "")).strip() if student_num_col else ""
            email = f"{user_id}@{self.EMAIL_DOMAIN}"
            records.append(
                {
                    "email": email,
                    "user_id": user_id,
                    "name": name,
                    "student_number": student_number,
                    "role": role,
                }
            )

        created = 0
        updated = 0
        conn = get_db_connection()
        cur = conn.cursor()
        for rec in records:
            cur.execute("SELECT * FROM students WHERE email = ?", (rec["email"],))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """
                    UPDATE students
                    SET name = ?, student_number = ?, user_id = ?, role = ?, last_active = CURRENT_TIMESTAMP
                    WHERE email = ?
                    """,
                    (rec["name"], rec["student_number"], rec["user_id"], rec["role"], rec["email"]),
                )
                updated += 1
            else:
                cur.execute(
                    """
                    INSERT INTO students (email, name, student_number, user_id, role)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rec["email"], rec["name"], rec["student_number"], rec["user_id"], rec["role"]),
                )
                created += 1
        conn.commit()
        conn.close()
        return {"ingested": len(records), "created": created, "updated": updated}

    def get_student(self, email: str) -> Dict[str, Any] | None:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE email = ?", (email,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_students(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY role DESC, name ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def progress_report(self, progress_service) -> Dict[str, Any]:
        students = self.list_students()
        report = []
        for s in students:
            p = progress_service.get_student_progress(s["email"])
            report.append(
                {
                    "email": s["email"],
                    "name": s.get("name"),
                    "student_number": s.get("student_number"),
                    "role": s.get("role"),
                    "content_pct": p["content"]["percentage"],
                    "assignments_pct": p["assignments"]["percentage"],
                    "quizzes_avg": p["quizzes"]["average_score"],
                    "quizzes_passed": p["quizzes"]["passed"],
                    "quizzes_attempted": p["quizzes"]["attempted"],
                }
            )
        return {"students": report}

    def quiz_report(self, quiz_service) -> Dict[str, Any]:
        # For simplicity, return topics and counts per student (could expand)
        return {"topics": quiz_service.COURSE_TOPICS if hasattr(quiz_service, "COURSE_TOPICS") else {}}

    def assignment_report(self, progress_service) -> Dict[str, Any]:
        # Placeholder: reuse progress data; could expand to per-assignment stats
        students = self.list_students()
        rows = []
        for s in students:
            assignments = progress_service.get_assignments(s["email"])
            rows.append({"email": s["email"], "assignments": assignments})
        return {"students": rows}

