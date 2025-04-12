import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from .university_provider import UniversityProvider
from ..mappers.university_mapper import UniversityMapper

class KevinUniversityAdapter(UniversityProvider):
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("external_services.kevin.base_url")
        self.api_key = config.get("external_services.kevin.api_key")
        self.timeout_seconds = config.get("external_services.kevin.timeout_seconds", 5)
        self.retry_attempts = config.get("external_services.kevin.retry_attempts", 3)
        self.logger = logging.getLogger(__name__)
        self.mapper = UniversityMapper()
        self.client_session: Optional[aiohttp.ClientSession] = None
        self._is_available = False
        self._last_error: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the adapter and check API availability"""
        try:
            self.client_session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            # Test connection
            await self._check_availability()
            self.logger.info("Kevin University API initialized successfully")
        except Exception as e:
            self._is_available = False
            self._last_error = str(e)
            self.logger.warning(f"Failed to initialize Kevin University API: {e}")

    async def _check_availability(self) -> bool:
        """Check if the Kevin API is available"""
        try:
            async with self.client_session.get(
                f"{self.base_url}/health",
                timeout=self.timeout_seconds
            ) as response:
                if response.status == 200:
                    self._is_available = True
                    self._last_error = None
                    return True
                else:
                    self._is_available = False
                    self._last_error = f"API health check failed with status {response.status}"
                    return False
        except Exception as e:
            self._is_available = False
            self._last_error = str(e)
            return False

    async def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff time"""
        return min(2 ** attempt, 10)  # Max 10 seconds

    async def get_universities(self, profile_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get university recommendations with retry logic"""
        if not self._is_available:
            self.logger.warning("Kevin University API is not available, skipping recommendations")
            return []

        for attempt in range(self.retry_attempts):
            try:
                async with self.client_session.post(
                    f"{self.base_url}/api/search/documents",
                    json={"profile": profile_data, "limit": limit},
                    timeout=self.timeout_seconds
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.mapper.map_universities(data)
                    else:
                        self.logger.warning(f"Kevin API request failed with status {response.status}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(await self._calculate_backoff(attempt))
                            continue
                        return []
            except asyncio.TimeoutError:
                self.logger.warning(f"Kevin API timeout (attempt {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(await self._calculate_backoff(attempt))
                    continue
                return []
            except Exception as e:
                self.logger.error(f"Unexpected error querying Kevin API: {e}")
                return []
        return []

    async def get_university_details(self, university_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific university"""
        if not self._is_available:
            self.logger.warning("Kevin University API is not available, skipping details request")
            return {}

        try:
            async with self.client_session.get(
                f"{self.base_url}/api/universities/{university_id}",
                timeout=self.timeout_seconds
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.mapper.map_university_details(data)
                else:
                    self.logger.warning(f"Failed to get university details: status {response.status}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error getting university details: {e}")
            return {}

    async def shutdown(self) -> None:
        """Clean up resources"""
        if self.client_session:
            await self.client_session.close()

    @property
    def is_available(self) -> bool:
        """Check if the provider is available"""
        return self._is_available

    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error 