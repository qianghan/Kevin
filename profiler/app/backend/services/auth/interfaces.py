"""
Authentication service interfaces.

This module defines the interfaces for authentication services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class AuthenticationServiceInterface(ABC):
    """Interface for authentication services."""
    
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Dictionary containing user information and tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an authentication token.
        
        Args:
            token: Authentication token to validate
            
        Returns:
            Dictionary containing token information
            
        Raises:
            AuthenticationError: If token is invalid
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an authentication token.
        
        Args:
            refresh_token: Refresh token to use
            
        Returns:
            Dictionary containing new tokens
            
        Raises:
            AuthenticationError: If refresh fails
        """
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get permissions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of permission strings
            
        Raises:
            AuthenticationError: If user not found
        """
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Dictionary containing created user information
            
        Raises:
            AuthenticationError: If user creation fails
        """
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user.
        
        Args:
            user_id: ID of the user to update
            user_data: Dictionary containing updated user information
            
        Returns:
            Dictionary containing updated user information
            
        Raises:
            AuthenticationError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """Delete a user.
        
        Args:
            user_id: ID of the user to delete
            
        Raises:
            AuthenticationError: If deletion fails
        """
        pass 