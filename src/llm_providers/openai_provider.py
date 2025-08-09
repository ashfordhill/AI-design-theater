"""OpenAI LLM provider implementation."""

import openai
from typing import List, Dict, Any, Optional
from ..models import ConversationMessage, PersonalityConfig, MessageRole
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_response(
        self,
        messages: List[ConversationMessage],
        personality: PersonalityConfig,
        context: Optional[str] = None
    ) -> str:
        """Generate a response using OpenAI's API."""
        formatted_messages = self.format_messages(messages)
        
        # Add system prompt
        system_message = {"role": "system", "content": personality.system_prompt}
        if context:
            system_message["content"] += f"\n\nAdditional context: {context}"
        
        formatted_messages.insert(0, system_message)
        
        try:
            response = await self.client.chat.completions.create(
                model=personality.model,
                messages=formatted_messages,
                temperature=personality.temperature,
                max_tokens=personality.max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            meta = f"model={personality.model} name={personality.name}"
            raise Exception(f"OpenAI API error ({meta}): {str(e)}")
    
    def format_messages(self, messages: List[ConversationMessage]) -> List[Dict[str, Any]]:
        """Format messages for OpenAI API."""
        formatted = []
        for msg in messages:
            if msg.role != MessageRole.SYSTEM:  # System messages handled separately
                formatted.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        return formatted
    
    async def validate_connection(self) -> bool:
        """Validate OpenAI connection."""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False