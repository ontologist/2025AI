"""Service for generating and managing adaptive quizzes using Ollama."""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import random
import re
from app.models.database import get_db_connection
from app.services.ollama_service import OllamaService
from app.services.progress_service import ProgressService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Course topics by week for quiz generation
COURSE_TOPICS = {
    1: {"en": "History of AI - Early developments, Turing Test", "ja": "AIの歴史 - 初期の発展、チューリングテスト"},
    2: {"en": "History of AI - AI winters, Expert systems", "ja": "AIの歴史 - AIの冬、エキスパートシステム"},
    3: {"en": "History of AI - Deep learning revolution", "ja": "AIの歴史 - ディープラーニング革命"},
    4: {"en": "Search algorithms - BFS and DFS", "ja": "探索アルゴリズム - 幅優先・深さ優先探索"},
    5: {"en": "Search algorithms - Best-first, A*", "ja": "探索アルゴリズム - 最良優先、A*"},
    6: {"en": "Game theory - Minimax, Alpha-beta pruning", "ja": "ゲーム理論 - ミニマックス、アルファベータ枝刈り"},
    7: {"en": "Probability and Bayes' theorem", "ja": "確率論とベイズの定理"},
    8: {"en": "Clustering and unsupervised learning", "ja": "クラスタリングと教師なし学習"},
    9: {"en": "Overview of AI and Machine Learning", "ja": "AIと機械学習の概要"},
    10: {"en": "Supervised learning basics", "ja": "教師あり学習の基礎"},
    11: {"en": "Classification algorithms", "ja": "分類アルゴリズム"},
    12: {"en": "Machine learning algorithms", "ja": "機械学習アルゴリズム"},
    13: {"en": "Reinforcement learning", "ja": "強化学習"},
    14: {"en": "Comprehensive review", "ja": "総合復習"},
}


class QuizService:
    """Service for generating and managing adaptive quizzes."""
    
    def __init__(self):
        self.ollama = OllamaService(model=settings.OLLAMA_MODEL)
        self.progress_service = ProgressService()
    
    async def generate_quiz(
        self,
        email: str,
        week_number: Optional[int] = None,
        topic: Optional[str] = None,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate an adaptive quiz for a student.
        
        The quiz adapts based on:
        - Student's progress (which weeks they've viewed)
        - Previous quiz performance
        - Specified difficulty level
        """
        try:
            # Get student progress to determine appropriate topics
            progress = self.progress_service.get_student_progress(email)
            
            # Determine topic if not specified
            if not topic and not week_number:
                # Choose a topic based on viewed content
                viewed_weeks = self._get_viewed_weeks(email)
                if viewed_weeks:
                    week_number = random.choice(viewed_weeks)
                else:
                    week_number = 1  # Default to week 1
            
            if week_number and not topic:
                topic_info = COURSE_TOPICS.get(week_number, COURSE_TOPICS[1])
                topic = topic_info["en"]
            
            # Adjust difficulty based on previous performance
            adjusted_difficulty = self._adjust_difficulty(email, difficulty)
            
            # Generate questions using Ollama
            questions = await self._generate_questions(
                topic=topic,
                num_questions=num_questions,
                difficulty=adjusted_difficulty,
                week_number=week_number
            )
            
            # Store quiz in database
            quiz_id = self._store_quiz(email, week_number, topic, questions, adjusted_difficulty)
            
            return {
                "quiz_id": quiz_id,
                "topic": topic,
                "week_number": week_number,
                "difficulty": adjusted_difficulty,
                "num_questions": len(questions),
                "questions": questions,
                "time_limit_minutes": num_questions * 2  # 2 minutes per question
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            raise
    
    async def _generate_questions(
        self,
        topic: str,
        num_questions: int,
        difficulty: str,
        week_number: Optional[int] = None
    ) -> List[Dict]:
        """Generate quiz questions using Ollama."""
        
        difficulty_guidance = {
            "easy": "basic understanding, definitions, simple recall",
            "medium": "application of concepts, comparisons, analysis",
            "hard": "complex problem-solving, synthesis, evaluation"
        }
        
        prompt = f"""Generate exactly {num_questions} multiple-choice quiz questions about: {topic}

Difficulty level: {difficulty} ({difficulty_guidance.get(difficulty, 'medium level')})

Requirements:
1. Each question must have exactly 4 options (A, B, C, D)
2. Only one option should be correct
3. Questions should test understanding, not just memorization
4. Include a brief explanation for the correct answer

Format your response as a JSON array with this exact structure:
[
  {{
    "question": "The question text in English",
    "question_ja": "日本語での質問",
    "options": {{
      "A": "First option",
      "B": "Second option", 
      "C": "Third option",
      "D": "Fourth option"
    }},
    "options_ja": {{
      "A": "選択肢A（日本語）",
      "B": "選択肢B（日本語）",
      "C": "選択肢C（日本語）",
      "D": "選択肢D（日本語）"
    }},
    "correct_answer": "A",
    "explanation": "Brief explanation why this is correct",
    "explanation_ja": "正解の説明（日本語）"
  }}
]

Generate the questions now:"""

        try:
            response = await self.ollama.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=3000
            )
            
            # Parse JSON from response
            questions = self._parse_questions_json(response)
            questions = self._sanitize_questions(questions)
            
            if not questions or len(questions) < num_questions:
                # Fallback: generate simple questions
                questions = self._sanitize_questions(
                    self._generate_fallback_questions(topic, num_questions)
                )
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions with Ollama: {str(e)}")
            return self._sanitize_questions(
                self._generate_fallback_questions(topic, num_questions)
            )
    
    def _parse_questions_json(self, response: str) -> List[Dict]:
        """Parse questions JSON from Ollama response."""
        try:
            # Try to find JSON array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return []
    
    def _generate_fallback_questions(self, topic: str, num_questions: int) -> List[Dict]:
        """Generate fallback questions if Ollama fails."""
        # Simple fallback questions about AI basics
        fallback = [
            {
                "question": f"What is a key concept in {topic}?",
                "question_ja": f"{topic}の主要な概念は何ですか？",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "options_ja": {"A": "選択肢A", "B": "選択肢B", "C": "選択肢C", "D": "選択肢D"},
                "correct_answer": "A",
                "explanation": "This is a fallback question. Please try generating again.",
                "explanation_ja": "これはフォールバック問題です。再度生成してください。"
            }
        ]
        return fallback * num_questions

    def _sanitize_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix common spelling/encoding issues in generated questions."""
        return [self._sanitize_question_data(q) for q in questions]

    def _sanitize_question_data(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize text fields within a single question."""
        typo_patterns = {
            r"タ[Uu][Rr][Ii][Nn][Gg]": "チューリング",
            r"タuring": "チューリング",
        }

        def _fix(text: Any) -> Any:
            if not isinstance(text, str):
                return text
            fixed = text
            for pattern, replacement in typo_patterns.items():
                fixed = re.sub(pattern, replacement, fixed)
            return fixed

        for field in ["question", "question_ja", "explanation", "explanation_ja"]:
            if field in question:
                question[field] = _fix(question[field])

        for opt_field in ["options", "options_ja"]:
            if opt_field in question and isinstance(question[opt_field], dict):
                question[opt_field] = {k: _fix(v) for k, v in question[opt_field].items()}

        return question
    
    def _get_viewed_weeks(self, email: str) -> List[int]:
        """Get list of weeks the student has viewed content for."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT cc.week_number
            FROM page_views pv
            JOIN course_content cc ON pv.page_path = cc.page_path
            WHERE pv.student_email = ? AND cc.week_number > 0
            ORDER BY cc.week_number
        ''', (email,))
        
        weeks = [row['week_number'] for row in cursor.fetchall()]
        conn.close()
        
        return weeks if weeks else [1, 2, 3]  # Default to first 3 weeks
    
    def _adjust_difficulty(self, email: str, base_difficulty: str) -> str:
        """Adjust quiz difficulty based on student's performance."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get average quiz score
        cursor.execute('''
            SELECT AVG(percentage) as avg_score, COUNT(*) as count
            FROM quiz_attempts 
            WHERE student_email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or result['count'] < 2:
            return base_difficulty
        
        avg_score = result['avg_score'] or 50
        
        # Adjust difficulty based on performance
        if avg_score >= 85:
            return "hard"
        elif avg_score >= 70:
            return "medium"
        else:
            return "easy"
    
    def _store_quiz(
        self,
        email: str,
        week_number: Optional[int],
        topic: str,
        questions: List[Dict],
        difficulty: str
    ) -> int:
        """Store generated quiz in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quizzes (student_email, week_number, topic, questions_json, difficulty)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, week_number, topic, json.dumps(questions), difficulty))
        
        quiz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return quiz_id
    
    def get_quiz(self, quiz_id: int) -> Optional[Dict]:
        """Get a quiz by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,))
        quiz = cursor.fetchone()
        conn.close()
        
        if quiz:
            return {
                "quiz_id": quiz['id'],
                "topic": quiz['topic'],
                "week_number": quiz['week_number'],
                "difficulty": quiz['difficulty'],
                "questions": json.loads(quiz['questions_json']),
                "created_at": quiz['created_at']
            }
        return None
    
    async def submit_quiz(
        self,
        email: str,
        quiz_id: int,
        answers: Dict[int, str],
        time_taken: int = 0
    ) -> Dict[str, Any]:
        """
        Submit quiz answers and calculate score.
        
        Args:
            email: Student email
            quiz_id: Quiz ID
            answers: Dict mapping question index to answer (e.g., {0: "A", 1: "B"})
            time_taken: Time taken in seconds
        """
        quiz = self.get_quiz(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")
        
        questions = quiz['questions']
        correct = 0
        results = []
        
        for i, question in enumerate(questions):
            student_answer = answers.get(i, answers.get(str(i), "")) or ""
            is_correct = student_answer.upper() == question['correct_answer'].upper()
            
            if is_correct:
                correct += 1
            
            results.append({
                "question_index": i,
                "student_answer": student_answer,
                "correct_answer": question['correct_answer'],
                "is_correct": is_correct,
                "explanation": question.get('explanation', ''),
                "explanation_ja": question.get('explanation_ja', '')
            })
        
        max_score = len(questions)
        percentage = (correct / max_score * 100) if max_score > 0 else 0
        
        # Store attempt
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quiz_attempts 
            (student_email, quiz_id, answers_json, score, max_score, percentage, time_taken_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email, quiz_id, json.dumps(answers), correct, max_score, percentage, time_taken))
        
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "attempt_id": attempt_id,
            "quiz_id": quiz_id,
            "score": correct,
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "passed": percentage >= 70,
            "results": results,
            "time_taken_seconds": time_taken
        }
    
    def get_quiz_history(self, email: str) -> List[Dict]:
        """Get quiz attempt history for a student."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT qa.*, q.topic, q.week_number, q.difficulty
            FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            WHERE qa.student_email = ?
            ORDER BY qa.completed_at DESC
        ''', (email,))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    async def close(self):
        """Clean up resources."""
        await self.ollama.close()

