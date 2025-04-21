"""Question model definitions."""

class Question:
    """Question model representing a Q&A question."""
    
    def __init__(self, id=None, text=None, type=None, category=None, target_field=None):
        """Initialize a question."""
        self.id = id
        self.text = text
        self.type = type
        self.category = category
        self.target_field = target_field
        self.importance = 0.5
        
    def to_dict(self):
        """Convert question to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type,
            "category": self.category,
            "target_field": self.target_field,
            "importance": self.importance
        } 