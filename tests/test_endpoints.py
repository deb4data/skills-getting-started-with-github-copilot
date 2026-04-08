"""
Tests for FastAPI backend endpoints.

Covers all endpoints:
- GET /
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister

Each test follows the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the code being tested
- Assert: Verify the results

Tests cover:
- Happy path (successful operations)
- Error scenarios (validation failures)
"""

import pytest


class TestRoot:
    """Tests for GET / endpoint (root redirect)."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to /static/index.html."""
        # Arrange
        # (No special arrangement needed; client fixture is pre-configured)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint (list all activities)."""

    def test_get_all_activities(self, client):
        """Test that /activities returns all available activities."""
        # Arrange
        # (Sample activities loaded via client fixture)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_structure(self, client):
        """Test that activity data has the correct structure."""
        # Arrange
        expected_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        # Assert
        for field in expected_fields:
            assert field in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_activities_contain_participants(self, client):
        """Test that activities contain the expected participants."""
        # Arrange
        expected_chess_participants = [
            "michael@mergington.edu",
            "daniel@mergington.edu"
        ]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_participants = data["Chess Club"]["participants"]
        
        # Assert
        for participant in expected_chess_participants:
            assert participant in chess_participants


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client):
        """Test successful signup for an activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_signup_appears_in_participants(self, client):
        """Test that a newly signed-up student appears in the participants list."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Programming Class"
        
        # Act: Sign up the student
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Act: Fetch the activities list
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert email in data[activity]["participants"]

    def test_duplicate_signup_rejected(self, client):
        """Test that signing up twice for the same activity is rejected."""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test that signup to non-existent activity returns 404."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    def test_signup_preserves_other_participants(self, client):
        """Test that new signup doesn't affect other participants."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"].copy()
        
        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        
        # Assert: All original participants are still there
        for original_email in initial_participants:
            assert original_email in updated_participants


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity."""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregistration removes the student from participants."""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act
        client.delete(f"/activities/{activity}/unregister", params={"email": email})
        
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert email not in data[activity]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test that unregister from non-existent activity returns 404."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    def test_unregister_non_enrolled_student(self, client):
        """Test that unregistering a non-enrolled student returns 400."""
        # Arrange
        email = "notenrolled@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"].lower()

    def test_unregister_preserves_other_participants(self, client):
        """Test that unregister doesn't affect other participants."""
        # Arrange
        email_to_remove = "daniel@mergington.edu"
        activity = "Chess Club"
        
        initial_response = client.get("/activities")
        remaining_participants = [
            p for p in initial_response.json()[activity]["participants"]
            if p != email_to_remove
        ]
        
        # Act
        client.delete(f"/activities/{activity}/unregister", params={"email": email_to_remove})
        
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        
        # Assert: Remaining students are still there
        for remaining_email in remaining_participants:
            assert remaining_email in updated_participants


class TestIntegration:
    """Integration tests for complex scenarios."""

    def test_signup_then_unregister(self, client):
        """Test complete signup and unregister workflow."""
        # Arrange
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Act & Assert: Initially, student is not signed up
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Act: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Signup succeeded
        assert signup_response.status_code == 200
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Unregister succeeded
        assert unregister_response.status_code == 200
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple students signing up and unregistering."""
        # Arrange
        activity = "Gym Class"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Act: Sign up multiple students
        for student in students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Assert: All are signed up
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for student in students:
            assert student in participants
        
        # Act: Unregister one student
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": students[0]}
        )
        
        # Assert: Only that one was removed, others remain
        assert unregister_response.status_code == 200
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert students[0] not in participants
        assert students[1] in participants
        assert students[2] in participants
