"""Profile test fixtures."""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

@pytest.fixture
def sample_profile():
    """Create a sample profile for testing."""
    profile = SimpleNamespace()
    profile.id = "profile123"
    profile.name = "John Doe"
    profile.email = "john.doe@example.com"
    
    # Add skills
    profile.skills = [
        SimpleNamespace(
            id=f"skill{i}", 
            name=name, 
            level="Advanced" if i < 2 else "Intermediate"
        ) 
        for i, name in enumerate(["Python", "JavaScript", "SQL", "React"])
    ]
    
    # Add experiences
    profile.experiences = [
        SimpleNamespace(
            id=f"exp{i}",
            company=company,
            position=position,
            description=f"Worked on various {company} projects",
            years=5 - i
        )
        for i, (company, position) in enumerate([
            ("Tech Corp", "Senior Developer"),
            ("Data Inc", "Data Analyst")
        ])
    ]
    
    # Add educations
    profile.educations = [
        SimpleNamespace(
            id="edu1",
            institution="University of Technology",
            degree="Bachelor's",
            field="Computer Science",
            year=2015
        )
    ]
    
    # Add to_dict method
    profile.to_dict = lambda: {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "skills": [{"id": s.id, "name": s.name, "level": s.level} for s in profile.skills],
        "experiences": [{"id": e.id, "company": e.company, "position": e.position, "years": e.years} for e in profile.experiences],
        "educations": [{"id": e.id, "institution": e.institution, "degree": e.degree, "field": e.field, "year": e.year} for e in profile.educations]
    }
    
    return profile

@pytest.fixture
def incomplete_profile():
    """Create an incomplete profile for testing."""
    profile = SimpleNamespace()
    profile.id = "profile456"
    profile.name = "Jane Smith"
    # Missing email
    
    # Add only one skill
    profile.skills = [
        SimpleNamespace(
            id="skill1", 
            name="Python", 
            level="Intermediate"
        )
    ]
    
    # Missing experiences
    profile.experiences = []
    
    # Incomplete education
    profile.educations = [
        SimpleNamespace(
            id="edu1",
            institution="University",
            # Missing degree and field
            year=2018
        )
    ]
    
    # Add incomplete fields methods
    profile.get_incomplete_fields = lambda: ["email", "experiences", "education_details"]
    profile.get_critical_incomplete_fields = lambda: ["email", "experiences"]
    
    # Add to_dict method
    profile.to_dict = lambda: {
        "id": profile.id,
        "name": profile.name,
        "skills": [{"id": s.id, "name": s.name, "level": s.level} for s in profile.skills],
        "experiences": [],
        "educations": [{"id": e.id, "institution": e.institution, "year": e.year} for e in profile.educations]
    }
    
    return profile

@pytest.fixture
def empty_profile():
    """Create an empty profile for testing."""
    profile = SimpleNamespace()
    profile.id = "profile789"
    # Missing most fields
    
    # Empty collections
    profile.skills = []
    profile.experiences = []
    profile.educations = []
    
    # Add incomplete fields methods
    profile.get_incomplete_fields = lambda: ["name", "email", "skills", "experiences", "educations"]
    profile.get_critical_incomplete_fields = lambda: ["name", "email", "skills"]
    
    # Add to_dict method
    profile.to_dict = lambda: {
        "id": profile.id,
        "skills": [],
        "experiences": [],
        "educations": []
    }
    
    return profile

@pytest.fixture
def mock_profile_repository():
    """Create a mock profile repository for testing."""
    mock_repo = MagicMock()
    
    # Configure mock methods
    mock_repo.get_profile.return_value = sample_profile()
    
    return mock_repo

@pytest.fixture
def profile_test_data():
    """Create test profile data for testing."""
    return {
        "profiles": [
            {
                "id": "p1",
                "name": "Test User",
                "email": "test@example.com",
                "user_id": "user456",
                "skills": ["Python", "JavaScript", "React"],
                "experience": [{"company": "Company X", "years": 5}],
                "education": [{"degree": "Bachelor's", "field": "Computer Science"}]
            }
        ],
        "predefined_questions": [
            {
                "id": "q1",
                "text": "Tell me about your technical skills",
                "category": "skills"
            },
            {
                "id": "q2", 
                "text": "Describe your work experience",
                "category": "professional"
            }
        ]
    } 