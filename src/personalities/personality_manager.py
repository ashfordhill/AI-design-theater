"""Personality management and provider factory."""

from typing import Dict, Optional
from ..models import PersonalityConfig, LLMProvider
from ..llm_providers import BaseLLMProvider, OpenAIProvider, AnthropicProvider


class PersonalityManager:
    """Manages AI personalities and their LLM providers."""
    
    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self._providers: Dict[LLMProvider, BaseLLMProvider] = {}
    
    def get_provider(self, provider_type: LLMProvider) -> BaseLLMProvider:
        """Get or create a provider instance."""
        if provider_type not in self._providers:
            if provider_type == LLMProvider.OPENAI:
                if not self.openai_api_key:
                    raise ValueError("OpenAI API key not provided")
                self._providers[provider_type] = OpenAIProvider(self.openai_api_key)
            elif provider_type == LLMProvider.ANTHROPIC:
                if not self.anthropic_api_key:
                    raise ValueError("Anthropic API key not provided")
                self._providers[provider_type] = AnthropicProvider(self.anthropic_api_key)
            else:
                raise ValueError(f"Unsupported provider: {provider_type}")
        
        return self._providers[provider_type]
    
    async def validate_personality(self, personality: PersonalityConfig) -> bool:
        """Validate that a personality's provider is accessible."""
        try:
            provider = self.get_provider(personality.provider)
            return await provider.validate_connection()
        except Exception:
            return False
    
    async def generate_response(
        self, 
        personality: PersonalityConfig, 
        messages: list, 
        context: Optional[str] = None
    ) -> str:
        """Generate a response for a given personality."""
        provider = self.get_provider(personality.provider)
        return await provider.generate_response(messages, personality, context)