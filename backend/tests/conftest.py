"""Pytest configuration and fixtures for AI-300 Bot tests."""
import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def temp_db_dir():
    """Create a temporary directory for test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def test_db_path(temp_db_dir):
    """Create a fresh test database for each test."""
    db_path = Path(temp_db_dir) / f"test_{os.getpid()}.db"
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function")
def mock_db_connection(test_db_path):
    """Mock database connection to use test database."""
    with patch('app.models.database.DB_PATH', test_db_path):
        # Initialize test database
        from app.models.database import init_database, get_db_connection
        init_database()
        yield get_db_connection


@pytest.fixture
def sample_student_email():
    """Sample student email for testing."""
    return "test.student@kwansei.ac.jp"


@pytest.fixture
def sample_page_view():
    """Sample page view data."""
    return {
        "page_path": "weeks/week-01/slides.html",
        "page_title": "Week 1: History of AI 1",
        "time_spent": 120
    }


@pytest.fixture
def sample_quiz_questions():
    """Sample quiz questions for testing."""
    return [
        {
            "question": "What is the Turing Test?",
            "question_ja": "チューリングテストとは何ですか？",
            "options": {
                "A": "A test to measure CPU speed",
                "B": "A test of a machine's ability to exhibit intelligent behavior",
                "C": "A programming language test",
                "D": "A memory test"
            },
            "options_ja": {
                "A": "CPU速度を測定するテスト",
                "B": "機械が知的行動を示す能力のテスト",
                "C": "プログラミング言語のテスト",
                "D": "メモリテスト"
            },
            "correct_answer": "B",
            "explanation": "The Turing Test evaluates a machine's ability to exhibit intelligent behavior indistinguishable from a human.",
            "explanation_ja": "チューリングテストは、機械が人間と区別できない知的行動を示す能力を評価します。"
        },
        {
            "question": "Who proposed the Turing Test?",
            "question_ja": "チューリングテストを提案したのは誰ですか？",
            "options": {
                "A": "John McCarthy",
                "B": "Alan Turing",
                "C": "Claude Shannon",
                "D": "Marvin Minsky"
            },
            "options_ja": {
                "A": "ジョン・マッカーシー",
                "B": "アラン・チューリング",
                "C": "クロード・シャノン",
                "D": "マービン・ミンスキー"
            },
            "correct_answer": "B",
            "explanation": "Alan Turing proposed the test in his 1950 paper.",
            "explanation_ja": "アラン・チューリングが1950年の論文でこのテストを提案しました。"
        }
    ]


@pytest.fixture
def mock_ollama_service():
    """Mock Ollama service for testing."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value='[{"question": "Test?", "question_ja": "テスト？", "options": {"A": "Yes", "B": "No", "C": "Maybe", "D": "None"}, "options_ja": {"A": "はい", "B": "いいえ", "C": "多分", "D": "なし"}, "correct_answer": "A", "explanation": "Test explanation", "explanation_ja": "テスト説明"}]')
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def test_client(mock_db_connection):
    """Create test client with mocked database."""
    from app.main import app
    from app.api.instructor import roster_service
    # Seed a default instructor for tests
    roster_service.ingest(
        pd.DataFrame(
            [
                {
                    "role": "Instructor",
                    "name": "Test Instructor",
                    "student_number": "",
                    "user_id": "instructor",
                }
            ]
        )
    )
    # Seed common test students
    test_emails = [
        "new.student@kwansei.ac.jp",
        "test@kwansei.ac.jp",
        "viewer@kwansei.ac.jp",
        "sync.test@kwansei.ac.jp",
        "empty.sync@kwansei.ac.jp",
        "percentage.test@kwansei.ac.jp",
        "botcount@kwansei.ac.jp",
        "nodupe@kwansei.ac.jp",
        "quiz.test@kwansei.ac.jp",
        "auto.topic@kwansei.ac.jp",
        "topic.test@kwansei.ac.jp",
        "get.quiz@kwansei.ac.jp",
        "submit.test@kwansei.ac.jp",
        "invalid.quiz@kwansei.ac.jp",
        "history.test@kwansei.ac.jp",
        "no.quizzes@kwansei.ac.jp",
        "zero.q@kwansei.ac.jp",
        "many.q@kwansei.ac.jp",
        "empty.answers@kwansei.ac.jp",
        "extra.answers@kwansei.ac.jp",
        "invalid.format@kwansei.ac.jp",
        "score.calc@kwansei.ac.jp",
        "round.test@kwansei.ac.jp",
        "history.order@kwansei.ac.jp",
        "multi.attempt@kwansei.ac.jp",
        "concurrent.test@kwansei.ac.jp",
        "unicode.test@kwansei.ac.jp",
        "null.test@kwansei.ac.jp",
        "zero.div@kwansei.ac.jp",
        "overflow@kwansei.ac.jp",
        "time.precision@kwansei.ac.jp",
        "status.consistency@kwansei.ac.jp",
        "count.accuracy@kwansei.ac.jp",
        "concurrent@kwansei.ac.jp",
    ]
    roster_service.ingest(
        pd.DataFrame(
            [
                {
                    "role": "Enrolled Student",
                    "name": email.split("@")[0],
                    "student_number": "",
                    "user_id": email.split("@")[0],
                }
                for email in test_emails
            ]
        )
    )
    # Add special-case emails with subdomains/plus or other domains used in tests
    special_emails = [
        "test+tag@sub.kwansei.ac.jp",
        "test+quiz@sub.kwansei.ac.jp",
        "large.body@test.com",
        "test+tag@test.com",
    ]
    conn = mock_db_connection()
    cur = conn.cursor()
    for email in special_emails:
        cur.execute(
            "INSERT OR IGNORE INTO students (email, name, role) VALUES (?, ?, 'student')",
            (email, email.split("@")[0]),
        )
    conn.commit()
    conn.close()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def assignment_grading_service(temp_db_dir):
    """Grading service that writes submissions to a temp dir."""
    from pathlib import Path
    from app.services.assignment_grading_service import AssignmentGradingService
    return AssignmentGradingService(submissions_dir=Path(temp_db_dir))


@pytest.fixture
def progress_service(mock_db_connection, assignment_grading_service):
    """Create progress service with test database and temp grading service."""
    from app.services.progress_service import ProgressService
    return ProgressService(grading_service=assignment_grading_service)


@pytest.fixture
def quiz_service(mock_db_connection, mock_ollama_service):
    """Create quiz service with mocked dependencies."""
    with patch('app.services.quiz_service.OllamaService', return_value=mock_ollama_service):
        from app.services.quiz_service import QuizService
        service = QuizService()
        service.ollama = mock_ollama_service
        yield service


# Test data generators
def generate_test_emails(count=5):
    """Generate multiple test email addresses."""
    return [f"student{i}@kwansei.ac.jp" for i in range(count)]


def generate_test_pages():
    """Generate list of test page paths."""
    return [
        "weeks/week-01/slides.html",
        "weeks/week-02/slides.html",
        "weeks/week-03/slides.html",
        "weeks/week-04/slides.html",
        "weeks/week-05/slides.html",
    ]

