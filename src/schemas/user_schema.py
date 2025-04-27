"""
JSON schema definitions for user-related models.

These schemas are used for validating API requests and responses.
"""

# Notification preference schema
notification_preference_schema = {
    "type": "object",
    "properties": {
        "email": {
            "type": "boolean",
            "description": "Whether to receive email notifications"
        },
        "push": {
            "type": "boolean",
            "description": "Whether to receive push notifications"
        },
        "in_app": {
            "type": "boolean",
            "description": "Whether to receive in-app notifications"
        }
    }
}

# User JSON Schema
user_schema = {
    "type": "object",
    "required": ["id", "firstName", "lastName", "email", "role", "createdAt", "updatedAt"],
    "properties": {
        "id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique identifier for the user"
        },
        "firstName": {
            "type": "string", 
            "minLength": 1,
            "description": "User's first name"
        },
        "lastName": {
            "type": "string",
            "minLength": 1,
            "description": "User's last name"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "User's email address"
        },
        "role": {
            "type": "string",
            "enum": ["student", "parent", "counselor", "admin"],
            "description": "User's role in the system"
        },
        "preferences": {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "enum": ["light", "dark", "system"],
                    "description": "User's preferred theme"
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "zh", "fr"],
                    "description": "User's preferred language"
                },
                "notifications": {
                    "type": "object",
                    "properties": {
                        "chat": notification_preference_schema,
                        "system": notification_preference_schema,
                        "updates": notification_preference_schema
                    }
                }
            }
        },
        "createdAt": {
            "type": "string",
            "format": "date-time",
            "description": "When the user was created"
        },
        "updatedAt": {
            "type": "string",
            "format": "date-time",
            "description": "When the user was last updated"
        }
    }
}

# User creation request schema
user_create_schema = {
    "type": "object",
    "required": ["firstName", "lastName", "email", "password", "role"],
    "properties": {
        "firstName": {
            "type": "string",
            "minLength": 1,
            "description": "User's first name"
        },
        "lastName": {
            "type": "string",
            "minLength": 1,
            "description": "User's last name"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "User's email address"
        },
        "password": {
            "type": "string",
            "minLength": 8,
            "description": "User's password"
        },
        "role": {
            "type": "string",
            "enum": ["student", "parent", "counselor", "admin"],
            "description": "User's role in the system"
        }
    }
}

# User update request schema
user_update_schema = {
    "type": "object",
    "properties": {
        "firstName": {
            "type": "string",
            "minLength": 1,
            "description": "User's first name"
        },
        "lastName": {
            "type": "string",
            "minLength": 1,
            "description": "User's last name"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "User's email address"
        },
        "preferences": {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "enum": ["light", "dark", "system"],
                    "description": "User's preferred theme"
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "zh", "fr"],
                    "description": "User's preferred language"
                },
                "notifications": {
                    "type": "object",
                    "properties": {
                        "chat": notification_preference_schema,
                        "system": notification_preference_schema,
                        "updates": notification_preference_schema
                    }
                }
            }
        }
    }
}

# User login request schema
user_login_schema = {
    "type": "object",
    "required": ["email", "password"],
    "properties": {
        "email": {
            "type": "string",
            "format": "email",
            "description": "User's email address"
        },
        "password": {
            "type": "string",
            "description": "User's password"
        },
        "rememberMe": {
            "type": "boolean",
            "description": "Whether to remember the user's login"
        }
    }
}

# User login response schema
user_login_response_schema = {
    "type": "object",
    "required": ["token", "user"],
    "properties": {
        "token": {
            "type": "string",
            "description": "Authentication token"
        },
        "user": user_schema
    }
} 