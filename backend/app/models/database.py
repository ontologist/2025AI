"""SQLite database setup and models for student progress tracking."""
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "student_progress.db"


def get_db_connection():
    """Get a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Students table - stores student info from roster/auth
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            student_number TEXT,
            user_id TEXT,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Page views table - tracks which pages/slides students have viewed
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            page_path TEXT NOT NULL,
            page_title TEXT,
            view_count INTEGER DEFAULT 1,
            first_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_spent_seconds INTEGER DEFAULT 0,
            UNIQUE(student_email, page_path)
        )
    ''')
    
    # Bot interactions table - tracks questions asked to the bot
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            question TEXT NOT NULL,
            response TEXT,
            language TEXT DEFAULT 'ja',
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assignments table - defines available assignments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            title_ja TEXT,
            description TEXT,
            max_score INTEGER DEFAULT 100,
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assignment submissions table - tracks completed assignments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            assignment_id INTEGER NOT NULL,
            status TEXT DEFAULT 'not_started',
            score INTEGER,
            submitted_at TIMESTAMP,
            graded_at TIMESTAMP,
            feedback TEXT,
            submission_path TEXT,
            UNIQUE(student_email, assignment_id),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id)
        )
    ''')
    
    # Quizzes table - stores generated quizzes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            week_number INTEGER,
            topic TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            difficulty TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Quiz attempts table - tracks quiz submissions and scores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            quiz_id INTEGER NOT NULL,
            answers_json TEXT NOT NULL,
            score INTEGER,
            max_score INTEGER,
            percentage REAL,
            time_taken_seconds INTEGER,
            started_at TIMESTAMP,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    ''')
    
    # Course content table - defines all trackable content pages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_path TEXT UNIQUE NOT NULL,
            page_title TEXT NOT NULL,
            page_title_ja TEXT,
            week_number INTEGER,
            content_type TEXT,
            is_required INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()

    # Ensure new columns exist on students table
    cursor.execute("PRAGMA table_info(students)")
    cols = {row["name"] for row in cursor.fetchall()}
    for col, ddl in [
        ("student_number", "ALTER TABLE students ADD COLUMN student_number TEXT"),
        ("user_id", "ALTER TABLE students ADD COLUMN user_id TEXT"),
        ("role", "ALTER TABLE students ADD COLUMN role TEXT DEFAULT 'student'"),
    ]:
        if col not in cols:
            try:
                cursor.execute(ddl)
            except Exception:
                pass
    conn.commit()
    
    # Initialize course content if empty
    cursor.execute('SELECT COUNT(*) FROM course_content')
    if cursor.fetchone()[0] == 0:
        _init_course_content(cursor)
        conn.commit()
    
    # Initialize assignments if empty
    cursor.execute('SELECT COUNT(*) FROM assignments')
    if cursor.fetchone()[0] == 0:
        _init_assignments(cursor)
        conn.commit()
    
    conn.close()
    logger.info("Database initialized successfully")


def _init_course_content(cursor):
    """Initialize the course content table with all trackable pages."""
    content = [
        # Week 1-7 slides
        ('weeks/week-01/slides.html', 'Week 1: History of AI 1', '第1週：人工知能の歴史1', 1, 'slides', 1),
        ('weeks/week-02/slides.html', 'Week 2: History of AI 2', '第2週：人工知能の歴史2', 2, 'slides', 1),
        ('weeks/week-03/slides.html', 'Week 3: History of AI 3', '第3週：人工知能の歴史3', 3, 'slides', 1),
        ('weeks/week-04/slides.html', 'Week 4: BFS & DFS Search', '第4週：幅優先・深さ優先探索', 4, 'slides', 1),
        ('weeks/week-05/slides.html', 'Week 5: Best-first & A*', '第5週：最良優先・A*探索', 5, 'slides', 1),
        ('weeks/week-06/slides.html', 'Week 6: Game Theory', '第6週：ゲーム理論', 6, 'slides', 1),
        ('weeks/week-07/slides.html', 'Week 7: Probability & Bayes', '第7週：確率・ベイズ定理', 7, 'slides', 1),
        # Week 8-14 slides and lectures
        ('weeks/week-08/slides.html', 'Week 8: Clustering Slides', '第8週：クラスタリング（スライド）', 8, 'slides', 1),
        ('weeks/week-08/lecture.html', 'Week 8: Clustering Lecture', '第8週：クラスタリング（講義）', 8, 'lecture', 1),
        ('weeks/week-09/slides.html', 'Week 9: AI/ML Overview Slides', '第9週：AI/ML概論（スライド）', 9, 'slides', 1),
        ('weeks/week-09/lecture.html', 'Week 9: AI/ML Overview Lecture', '第9週：AI/ML概論（講義）', 9, 'lecture', 1),
        ('weeks/week-10/slides.html', 'Week 10: Supervised Learning Slides', '第10週：教師あり学習（スライド）', 10, 'slides', 1),
        ('weeks/week-10/lecture.html', 'Week 10: Supervised Learning Lecture', '第10週：教師あり学習（講義）', 10, 'lecture', 1),
        ('weeks/week-11/slides.html', 'Week 11: Classification Slides', '第11週：分類（スライド）', 11, 'slides', 1),
        ('weeks/week-11/lecture.html', 'Week 11: Classification Lecture', '第11週：分類（講義）', 11, 'lecture', 1),
        ('weeks/week-12/slides.html', 'Week 12: ML Algorithms Slides', '第12週：MLアルゴリズム（スライド）', 12, 'slides', 1),
        ('weeks/week-12/lecture.html', 'Week 12: ML Algorithms Lecture', '第12週：MLアルゴリズム（講義）', 12, 'lecture', 1),
        ('weeks/week-13/slides.html', 'Week 13: Reinforcement Learning Slides', '第13週：強化学習（スライド）', 13, 'slides', 1),
        ('weeks/week-13/lecture.html', 'Week 13: Reinforcement Learning Lecture', '第13週：強化学習（講義）', 13, 'lecture', 1),
        ('weeks/week-14/slides.html', 'Week 14: Final Review Slides', '第14週：最終復習（スライド）', 14, 'slides', 1),
        ('weeks/week-14/lecture.html', 'Week 14: Study Guide', '第14週：学習ガイド', 14, 'lecture', 1),
        # Main page
        ('index.html', 'Course Homepage', 'コースホームページ', 0, 'main', 1),
    ]
    
    cursor.executemany('''
        INSERT INTO course_content (page_path, page_title, page_title_ja, week_number, content_type, is_required)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', content)


def _init_assignments(cursor):
    """Initialize the assignments table with course assignments."""
    assignments = [
        (8, 'Week 8 Assignment: Clustering Analysis', '第8週課題：クラスタリング分析', 'Apply clustering concepts to real-world data', 100),
        (9, 'Week 9 Assignment: AI/ML Reflection', '第9週課題：AI/ML振り返り', 'Reflect on AI and ML applications', 100),
        (10, 'Week 10 Assignment: Supervised Learning', '第10週課題：教師あり学習', 'Practice supervised learning concepts', 100),
        (11, 'Week 11 Assignment: Classification', '第11週課題：分類', 'Classification problem analysis', 100),
        (12, 'Week 12 Assignment: Algorithm Analysis', '第12週課題：アルゴリズム分析', 'Analyze ML algorithms', 100),
        (13, 'Week 13 Assignment: Reinforcement Learning', '第13週課題：強化学習', 'RL concepts and applications', 100),
    ]
    
    cursor.executemany('''
        INSERT INTO assignments (week_number, title, title_ja, description, max_score)
        VALUES (?, ?, ?, ?, ?)
    ''', assignments)


# Initialize database on module import
init_database()

