"""Service for tracking and managing student progress."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.models.database import get_db_connection
import logging

logger = logging.getLogger(__name__)


class ProgressService:
    """Service for managing student progress tracking."""
    
    def __init__(self):
        pass
    
    def get_or_create_student(self, email: str, name: Optional[str] = None) -> Dict:
        """Get or create a student record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students WHERE email = ?', (email,))
        student = cursor.fetchone()
        
        if not student:
            cursor.execute(
                'INSERT INTO students (email, name) VALUES (?, ?)',
                (email, name)
            )
            conn.commit()
            cursor.execute('SELECT * FROM students WHERE email = ?', (email,))
            student = cursor.fetchone()
        else:
            # Update last active
            cursor.execute(
                'UPDATE students SET last_active = CURRENT_TIMESTAMP WHERE email = ?',
                (email,)
            )
            conn.commit()
        
        conn.close()
        return dict(student)
    
    def record_page_view(self, email: str, page_path: str, page_title: str = "", time_spent: int = 0) -> Dict:
        """Record a page view for a student."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if view exists
        cursor.execute(
            'SELECT * FROM page_views WHERE student_email = ? AND page_path = ?',
            (email, page_path)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE page_views 
                SET view_count = view_count + 1,
                    last_viewed = CURRENT_TIMESTAMP,
                    time_spent_seconds = time_spent_seconds + ?
                WHERE student_email = ? AND page_path = ?
            ''', (time_spent, email, page_path))
        else:
            cursor.execute('''
                INSERT INTO page_views (student_email, page_path, page_title, time_spent_seconds)
                VALUES (?, ?, ?, ?)
            ''', (email, page_path, page_title, time_spent))
        
        conn.commit()
        conn.close()
        
        return {"status": "recorded", "page_path": page_path}
    
    def record_bot_interaction(self, email: str, question: str, response: str, language: str = "ja", topic: str = None) -> Dict:
        """Record a bot interaction."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bot_interactions (student_email, question, response, language, topic)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, question, response, language, topic))
        
        conn.commit()
        interaction_id = cursor.lastrowid
        conn.close()
        
        return {"status": "recorded", "interaction_id": interaction_id}
    
    def get_student_progress(self, email: str) -> Dict[str, Any]:
        """Get comprehensive progress for a student."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total required content count
        cursor.execute('SELECT COUNT(*) FROM course_content WHERE is_required = 1')
        total_content = cursor.fetchone()[0]
        
        # Get viewed content count
        cursor.execute('''
            SELECT COUNT(DISTINCT pv.page_path) 
            FROM page_views pv
            JOIN course_content cc ON pv.page_path = cc.page_path
            WHERE pv.student_email = ? AND cc.is_required = 1
        ''', (email,))
        viewed_content = cursor.fetchone()[0]
        
        # Get bot interactions count
        cursor.execute(
            'SELECT COUNT(*) FROM bot_interactions WHERE student_email = ?',
            (email,)
        )
        bot_questions = cursor.fetchone()[0]
        
        # Get total assignments
        cursor.execute('SELECT COUNT(*) FROM assignments')
        total_assignments = cursor.fetchone()[0]
        
        # Get completed assignments
        cursor.execute('''
            SELECT COUNT(*) FROM assignment_submissions 
            WHERE student_email = ? AND status = 'completed'
        ''', (email,))
        completed_assignments = cursor.fetchone()[0]
        
        # Get total quizzes attempted
        cursor.execute('''
            SELECT COUNT(DISTINCT quiz_id) FROM quiz_attempts 
            WHERE student_email = ?
        ''', (email,))
        quizzes_attempted = cursor.fetchone()[0]
        
        # Get quizzes passed (>=70%)
        cursor.execute('''
            SELECT COUNT(*) FROM quiz_attempts 
            WHERE student_email = ? AND percentage >= 70
        ''', (email,))
        quizzes_passed = cursor.fetchone()[0]
        
        # Get average quiz score
        cursor.execute('''
            SELECT AVG(percentage) FROM quiz_attempts 
            WHERE student_email = ?
        ''', (email,))
        avg_quiz_score = cursor.fetchone()[0] or 0
        
        # Get detailed page views by week
        cursor.execute('''
            SELECT cc.week_number, COUNT(DISTINCT pv.page_path) as viewed,
                   (SELECT COUNT(*) FROM course_content WHERE week_number = cc.week_number AND is_required = 1) as total
            FROM course_content cc
            LEFT JOIN page_views pv ON cc.page_path = pv.page_path AND pv.student_email = ?
            WHERE cc.is_required = 1
            GROUP BY cc.week_number
            ORDER BY cc.week_number
        ''', (email,))
        weekly_progress = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Calculate percentages
        content_percentage = (viewed_content / total_content * 100) if total_content > 0 else 0
        assignment_percentage = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        
        return {
            "email": email,
            "content": {
                "viewed": viewed_content,
                "total": total_content,
                "percentage": round(content_percentage, 1)
            },
            "bot_interactions": {
                "count": bot_questions
            },
            "assignments": {
                "completed": completed_assignments,
                "total": total_assignments,
                "percentage": round(assignment_percentage, 1)
            },
            "quizzes": {
                "attempted": quizzes_attempted,
                "passed": quizzes_passed,
                "average_score": round(avg_quiz_score, 1)
            },
            "weekly_progress": weekly_progress
        }
    
    def get_viewed_pages(self, email: str) -> List[str]:
        """Get list of pages viewed by student."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT page_path FROM page_views WHERE student_email = ?',
            (email,)
        )
        pages = [row['page_path'] for row in cursor.fetchall()]
        conn.close()
        
        return pages
    
    def submit_assignment(self, email: str, assignment_id: int, status: str = "submitted") -> Dict:
        """Submit or update an assignment."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assignment_submissions (student_email, assignment_id, status, submitted_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_email, assignment_id) DO UPDATE SET
                status = excluded.status,
                submitted_at = CURRENT_TIMESTAMP
        ''', (email, assignment_id, status))
        
        conn.commit()
        conn.close()
        
        return {"status": "submitted", "assignment_id": assignment_id}
    
    def get_assignments(self, email: str) -> List[Dict]:
        """Get all assignments with student's submission status."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, 
                   COALESCE(s.status, 'not_started') as submission_status,
                   s.score,
                   s.submitted_at,
                   s.feedback
            FROM assignments a
            LEFT JOIN assignment_submissions s ON a.id = s.assignment_id AND s.student_email = ?
            ORDER BY a.week_number
        ''', (email,))
        
        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return assignments
    
    def sync_progress(self, email: str, local_data: Dict) -> Dict:
        """
        Sync local browser progress with server.
        Merges local data with server data, keeping the most complete record.
        """
        # Record any page views from local data
        if 'viewed_pages' in local_data:
            for page in local_data['viewed_pages']:
                self.record_page_view(email, page.get('path', ''), page.get('title', ''))
        
        # Get current server progress
        progress = self.get_student_progress(email)
        viewed_pages = self.get_viewed_pages(email)
        
        return {
            "progress": progress,
            "viewed_pages": viewed_pages,
            "synced_at": datetime.now().isoformat()
        }

