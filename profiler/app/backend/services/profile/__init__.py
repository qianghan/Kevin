"""
Profile Service Package.

This package provides a SOLID-compliant implementation of the Profile Service.
"""

from .service import ProfileService
from .factory import ProfileServiceFactory
from .models import Profile, ProfileState, ProfileSectionData, ProfileConfig
from .interfaces import (
    ProfileRepositoryInterface,
    ProfileValidatorInterface,
    ProfileStateCalculatorInterface,
    ProfileNotifierInterface,
    ProfileFactoryInterface
)
from .repository import JSONFileProfileRepository, DatabaseProfileRepository
from .validator import BasicProfileValidator
from .state import DefaultProfileStateCalculator
from .notifier import WebSocketProfileNotifier, MultiChannelProfileNotifier
# Import PostgreSQL implementations
from .database import PostgreSQLProfileRepository, DatabaseManager, Base, ProfileModel, ProfileSectionModel

__all__ = [
    # Main service
    'ProfileService',
    'ProfileServiceFactory',
    
    # Models
    'Profile',
    'ProfileState',
    'ProfileSectionData',
    'ProfileConfig',
    
    # Interfaces
    'ProfileRepositoryInterface',
    'ProfileValidatorInterface',
    'ProfileStateCalculatorInterface',
    'ProfileNotifierInterface',
    'ProfileFactoryInterface',
    
    # Implementations
    'JSONFileProfileRepository',
    'DatabaseProfileRepository',
    'BasicProfileValidator',
    'DefaultProfileStateCalculator',
    'WebSocketProfileNotifier',
    'MultiChannelProfileNotifier',
    
    # Database implementations
    'PostgreSQLProfileRepository',
    'DatabaseManager',
    'Base',
    'ProfileModel',
    'ProfileSectionModel'
] 