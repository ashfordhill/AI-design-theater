"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models import ConversationMessage, PersonalityConfig


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[ConversationMessage],
        personality: PersonalityConfig,
        context: Optional[str] = None
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def format_messages(self, messages: List[ConversationMessage]) -> List[Dict[str, Any]]:
        """Format messages for the specific provider's API."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the provider connection is working."""
        pass