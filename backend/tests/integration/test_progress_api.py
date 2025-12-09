"""Integration tests for Progress API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestProgressAPIEndpoints:
    """Integration tests for progress API."""
    
    def test_get_progress_new_student(self, test_client):
        """Test getting progress for new student."""
        response = test_client.get("/api/progress/new.student@kwansei.ac.jp")
        
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == "new.student@kwansei.ac.jp"
        assert data['content']['viewed'] == 0
    
    def test_get_progress_invalid_email_format(self, test_client):
        """Test getting progress with unusual email format."""
        response = test_client.get("/api/progress/not-an-email")
        
        # Should still work - email validation is at app level, not API
        assert response.status_code == 200
    
    def test_record_page_view(self, test_client):
        """Test recording a page view."""
        response = test_client.post(
            "/api/progress/page-view",
            json={
                "email": "test@kwansei.ac.jp",
                "page_path": "weeks/week-01/slides.html",
                "page_title": "Week 1",
                "time_spent": 60
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'recorded'
    
    def test_record_page_view_missing_email(self, test_client):
        """Test recording page view without email."""
        response = test_client.post(
            "/api/progress/page-view",
            json={
                "page_path": "test.html"
            }
        )
        
        # Should return 422 validation error
        assert response.status_code == 422
    
    def test_record_bot_interaction(self, test_client):
        """Test recording a bot interaction."""
        response = test_client.post(
            "/api/progress/bot-interaction",
            json={
                "email": "test@kwansei.ac.jp",
                "question": "What is AI?",
                "response": "AI is artificial intelligence.",
                "language": "en"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'recorded'
    
    def test_record_bot_interaction_japanese(self, test_client):
        """Test recording bot interaction with Japanese content."""
        response = test_client.post(
            "/api/progress/bot-interaction",
            json={
                "email": "test@kwansei.ac.jp",
                "question": "人工知能とは何ですか？",
                "response": "人工知能は機械が知的に振る舞うことです。",
                "language": "ja"
            }
        )
        
        assert response.status_code == 200
    
    def test_get_viewed_pages(self, test_client):
        """Test getting viewed pages for student."""
        email = "viewer@kwansei.ac.jp"
        
        # First record some views
        test_client.post(
            "/api/progress/page-view",
            json={"email": email, "page_path": "page1.html"}
        )
        test_client.post(
            "/api/progress/page-view",
            json={"email": email, "page_path": "page2.html"}
        )
        
        # Get viewed pages
        response = test_client.get(f"/api/progress/{email}/viewed-pages")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['viewed_pages']) == 2
    
    def test_get_assignments(self, test_client):
        """Test getting assignments list."""
        response = test_client.get("/api/progress/test@kwansei.ac.jp/assignments")
        
        assert response.status_code == 200
        data = response.json()
        assert 'assignments' in data
        assert len(data['assignments']) == 6  # 6 assignments
    
    def test_submit_assignment(self, test_client):
        """Test submitting an assignment."""
        # First get an assignment ID
        assignments_response = test_client.get("/api/progress/test@kwansei.ac.jp/assignments")
        assignment = assignments_response.json()['assignments'][0]
        assignment_id = assignment['id']
        week_number = assignment['week_number']
        
        response = test_client.post(
            "/api/progress/assignment/submit",
            json={
                "email": "test@kwansei.ac.jp",
                "assignment_id": assignment_id,
                "status": "submitted",
                "submission": {"answers": "Sample submission text"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'grading' in data

        # Progress should reflect submission status
        progress = test_client.get("/api/progress/test@kwansei.ac.jp").json()
        wk = next((w for w in progress["weekly_progress"] if w["week_number"] == week_number), None)
        assert wk is not None
        assert wk["assignment_status"] in ("submitted", "completed")
    
    def test_sync_progress(self, test_client):
        """Test syncing progress."""
        response = test_client.post(
            "/api/progress/sync",
            json={
                "email": "sync.test@kwansei.ac.jp",
                "local_data": {
                    "viewed_pages": [
                        {"path": "test1.html", "title": "Test 1"},
                        {"path": "test2.html", "title": "Test 2"}
                    ]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'progress' in data
        assert 'synced_at' in data
    
    def test_sync_progress_empty_data(self, test_client):
        """Test syncing with empty local data."""
        response = test_client.post(
            "/api/progress/sync",
            json={
                "email": "empty.sync@kwansei.ac.jp",
                "local_data": {}
            }
        )
        
        assert response.status_code == 200


class TestProgressAPIEdgeCases:
    """Edge case tests for Progress API."""
    
    def test_progress_special_characters_email(self, test_client):
        """Test progress with special characters in email."""
        email = "test+tag@sub.kwansei.ac.jp"
        response = test_client.get(f"/api/progress/{email}")
        
        # URL encoding should handle this
        assert response.status_code == 200
    
    def test_page_view_unicode_path(self, test_client):
        """Test page view with Unicode in path."""
        response = test_client.post(
            "/api/progress/page-view",
            json={
                "email": "test@kwansei.ac.jp",
                "page_path": "コース/第1週.html",
                "page_title": "日本語タイトル",
                "time_spent": 30
            }
        )
        
        assert response.status_code == 200
    
    def test_very_long_question(self, test_client):
        """Test recording very long bot question."""
        long_question = "A" * 10000
        
        response = test_client.post(
            "/api/progress/bot-interaction",
            json={
                "email": "test@kwansei.ac.jp",
                "question": long_question,
                "response": "Short response"
            }
        )
        
        assert response.status_code == 200
    
    def test_negative_time_spent(self, test_client):
        """Test page view with negative time spent."""
        response = test_client.post(
            "/api/progress/page-view",
            json={
                "email": "test@kwansei.ac.jp",
                "page_path": "test.html",
                "time_spent": -100
            }
        )
        
        # API should accept it - validation is elsewhere
        assert response.status_code == 200
    
    def test_concurrent_requests(self, test_client):
        """Test handling multiple concurrent-ish requests."""
        email = "concurrent@kwansei.ac.jp"
        
        # Simulate multiple rapid requests
        for i in range(10):
            response = test_client.post(
                "/api/progress/page-view",
                json={
                    "email": email,
                    "page_path": f"page{i}.html",
                    "time_spent": 10
                }
            )
            assert response.status_code == 200
        
        # All should have been recorded
        progress = test_client.get(f"/api/progress/{email}").json()
        assert progress['content']['viewed'] == 10


class TestProgressAPIRegressions:
    """Regression tests for known issues."""
    
    def test_progress_percentage_not_exceeds_100(self, test_client):
        """Regression: Ensure percentage never exceeds 100%."""
        email = "percentage.test@kwansei.ac.jp"
        
        # View more pages than total (if that were somehow possible)
        for i in range(30):
            test_client.post(
                "/api/progress/page-view",
                json={
                    "email": email,
                    "page_path": f"weeks/week-{i:02d}/slides.html"
                }
            )
        
        progress = test_client.get(f"/api/progress/{email}").json()
        
        assert progress['content']['percentage'] <= 100.0
    
    def test_bot_count_increments_correctly(self, test_client):
        """Regression: Ensure bot count increments for each interaction."""
        email = "botcount@kwansei.ac.jp"
        
        for i in range(5):
            test_client.post(
                "/api/progress/bot-interaction",
                json={
                    "email": email,
                    "question": f"Question {i}",
                    "response": f"Response {i}"
                }
            )
        
        progress = test_client.get(f"/api/progress/{email}").json()
        
        assert progress['bot_interactions']['count'] == 5
    
    def test_sync_doesnt_duplicate_pages(self, test_client):
        """Regression: Sync shouldn't create duplicate page views."""
        email = "nodupe@kwansei.ac.jp"
        
        # Record page view directly
        test_client.post(
            "/api/progress/page-view",
            json={"email": email, "page_path": "unique.html"}
        )
        
        # Sync with same page
        test_client.post(
            "/api/progress/sync",
            json={
                "email": email,
                "local_data": {
                    "viewed_pages": [{"path": "unique.html"}]
                }
            }
        )
        
        # Should only have 1 unique page
        viewed = test_client.get(f"/api/progress/{email}/viewed-pages").json()
        assert viewed['viewed_pages'].count("unique.html") == 1

