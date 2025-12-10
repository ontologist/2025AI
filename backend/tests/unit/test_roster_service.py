import pandas as pd
import tempfile
from unittest.mock import patch
from pathlib import Path
from app.services.roster_service import RosterService
from app.models import database


def test_normalize_role_and_email_domain():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        with patch("app.models.database.DB_PATH", db_path):
            database.init_database()
            service = RosterService()
            df = pd.DataFrame(
                [
                    {"role": "Instructor", "name": "Prof A", "student_number": "", "user_id": "inst01"},
                    {"role": "Enrolled Student", "name": "Stud B", "student_number": "12345", "user_id": "abc12345"},
                    {"role": "Participant", "name": "Stud C", "student_number": "67890", "user_id": "xyz67890"},
                ]
            )
            summary = service.ingest(df)
            assert summary["ingested"] == 3
            assert summary["created"] == 3

            inst = service.get_student("inst01@kwansei.ac.jp")
            assert inst["role"] == "instructor"
            stud = service.get_student("abc12345@kwansei.ac.jp")
            assert stud["role"] == "student"


def test_ingest_updates_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        with patch("app.models.database.DB_PATH", db_path):
            database.init_database()
            service = RosterService()
            df = pd.DataFrame([{"role": "Enrolled Student", "name": "Original", "student_number": "1", "user_id": "dup001"}])
            service.ingest(df)
            df2 = pd.DataFrame([{"role": "Participant", "name": "Updated", "student_number": "2", "user_id": "dup001"}])
            summary = service.ingest(df2)
            assert summary["updated"] == 1
            stud = service.get_student("dup001@kwansei.ac.jp")
            assert stud["name"] == "Updated"
            assert stud["student_number"] == "2"

