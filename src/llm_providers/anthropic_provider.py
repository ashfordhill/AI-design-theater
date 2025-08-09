"""Anthropic LLM provider implementation."""

import anthropic
from typing import List, Dict, Any, Optional
from ..models import ConversationMessage, PersonalityConfig, MessageRole
from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate_response(
        self,
        messages: List[ConversationMessage],
        personality: PersonalityConfig,
        context: Optional[str] = None
    ) -> str:
        """Generate a response using Anthropic's API."""
        formatted_messages = self.format_messages(messages)
        
        system_prompt = personality.system_prompt
        if context:
            system_prompt += f"\n\nAdditional context: {context}"
        
        try:
            response = await self.client.messages.create(
                model=personality.model,
                system=system_prompt,
                messages=formatted_messages,
                temperature=personality.temperature,
                max_tokens=personality.max_tokens or 4000
            )
            return response.content[0].text.strip()
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def format_messages(self, messages: List[ConversationMessage]) -> List[Dict[str, Any]]:
        """Format messages for Anthropic API."""
        formatted = []
        for msg in messages:
            if msg.role != MessageRole.SYSTEM:  # System messages handled separately
                formatted.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        return formatted
    
    async def validate_connection(self) -> bool:
        """Validate Anthropic connection."""
        try:
            # Simple test message
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False