import io
import pandas as pd
import pytest
from app.api.instructor import roster_service


class TestInstructorAPI:
    """Instructor endpoints: roster upload and reports."""

    def test_roster_upload_and_reports(self, test_client):
        # Ensure instructor seeded
        roster_service.ingest(
            pd.DataFrame([{"role": "Instructor", "name": "Seed", "student_number": "", "user_id": "instructor"}])
        )
        # Build roster with instructor and student
        df = pd.DataFrame(
            [
                {"role": "Instructor", "name": "Prof Test", "student_number": "", "user_id": "inst99"},
                {"role": "Enrolled Student", "name": "Alice", "student_number": "S001", "user_id": "abc12345"},
            ]
        )
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)

        files = {"file": ("roster.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = test_client.post(
            "/api/instructor/roster/upload",
            data={"instructor_email": "instructor@kwansei.ac.jp"},
            files=files,
        )
        assert resp.status_code == 200
        summary = resp.json()
        assert summary["ingested"] == 2

        # Progress report should include student
        progress = test_client.get(
            "/api/instructor/reports/progress",
            params={"instructor_email": "instructor@kwansei.ac.jp"},
        ).json()
        emails = [s["email"] for s in progress["students"]]
        assert "abc12345@kwansei.ac.jp" in emails

    def test_progress_rejects_unenrolled(self, test_client):
        resp = test_client.get("/api/progress/notenrolled@kwansei.ac.jp")
        assert resp.status_code == 403

