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
            # Defensive: Anthropic may return empty content array on some error edge cases
            try:
                if not getattr(response, 'content', None):
                    raise ValueError("Empty response content from Anthropic API")
                first = response.content[0]
                # Some SDK variants wrap text differently
                text = getattr(first, 'text', None) or getattr(first, 'value', None)
                if not text:
                    raise ValueError("No text field in first content block")
                return text.strip()
            except Exception as inner:
                raise Exception(f"Anthropic API malformed response: {inner}")
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