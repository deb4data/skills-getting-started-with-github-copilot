"""
Test configuration and fixtures for FastAPI backend tests.

Provides fixtures for:
- FastAPI app instance
- TestClient for making requests
- Sample activities data
- Temporary activities file for isolated testing
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.app import app, load_activities, save_activities


@pytest.fixture
def sample_activities_data():
    """Provides sample activities data for testing."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu"]
        }
    }


@pytest.fixture
def temp_activities_file(sample_activities_data):
    """
    Creates a temporary activities.json file for isolated testing.
    
    This fixture:
    1. Creates a temporary file with sample activities data
    2. Patches app.DATA_FILE to use the temporary file
    3. Resets app.activities to use the temporary data
    4. Cleans up after the test completes
    
    Returns the Path object for the temporary file.
    """
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False
    ) as tmp_file:
        json.dump(sample_activities_data, tmp_file)
        tmp_file_path = Path(tmp_file.name)
    
    # Patch the DATA_FILE in the app module to use the temporary file
    with patch('src.app.DATA_FILE', tmp_file_path):
        # Reload activities from the temporary file
        import src.app as app_module
        app_module.activities = load_activities()
        yield tmp_file_path
        # Clean up: restore original activities from real file
        app_module.activities = load_activities()
    
    # Delete the temporary file
    tmp_file_path.unlink()


@pytest.fixture
def client(temp_activities_file):
    """
    Provides a TestClient for making requests to the FastAPI app.
    
    Uses the temp_activities_file fixture to ensure tests have
    isolated, temporary data and don't modify the real activities.json.
    """
    return TestClient(app)
