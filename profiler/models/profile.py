"""Profile model definitions."""

class Profile:
    """Profile model representing a user's professional profile."""
    
    def __init__(self, id=None, name=None, email=None):
        """Initialize a profile."""
        self.id = id
        self.name = name
        self.email = email
        self.skills = []
        self.experiences = []
        self.educations = []
        
    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "skills": [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.skills],
            "experiences": [e.to_dict() if hasattr(e, 'to_dict') else e for e in self.experiences],
            "educations": [e.to_dict() if hasattr(e, 'to_dict') else e for e in self.educations],
        }
        
    def get_incomplete_fields(self):
        """Get list of incomplete fields in the profile."""
        incomplete = []
        
        if not self.name:
            incomplete.append("name")
        if not self.email:
            incomplete.append("email")
        if not self.skills:
            incomplete.append("skills")
        if not self.experiences:
            incomplete.append("experiences")
        if not self.educations:
            incomplete.append("educations")
            
        return incomplete
        
    def get_critical_incomplete_fields(self):
        """Get list of critical incomplete fields in the profile."""
        critical_fields = ["name", "email", "skills"]
        return [field for field in critical_fields if field in self.get_incomplete_fields()] 