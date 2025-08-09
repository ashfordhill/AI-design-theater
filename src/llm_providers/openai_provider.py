"""OpenAI LLM provider implementation.

Enhancements:
- Capture rate limit / quota headers when errors occur
- Provide clearer classification (quota vs rate-limit vs other)
- Support fallback model via OPENAI_FALLBACK_MODEL env var if primary fails with quota
"""

import openai
from typing import List, Dict, Any, Optional
import os
import hashlib
from ..models import ConversationMessage, PersonalityConfig, MessageRole
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = openai.AsyncOpenAI(api_key=api_key)
        try:
            fp = hashlib.sha256(api_key.encode()).hexdigest()[:8]
            print(f"[OpenAIProvider] Initialized client key_fp={fp}")
        except Exception:
            pass
    
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
        
        primary_model = personality.model
        fallback_model = os.getenv("OPENAI_FALLBACK_MODEL")
        attempted_models = []
        last_err: Optional[Exception] = None

        for model_choice in [primary_model, fallback_model] if fallback_model else [primary_model]:
            if model_choice in attempted_models or not model_choice:
                continue
            attempted_models.append(model_choice)
            try:
                response = await self.client.chat.completions.create(
                    model=model_choice,
                    messages=formatted_messages,
                    temperature=personality.temperature,
                    max_tokens=personality.max_tokens
                )
                if model_choice != primary_model:
                    print(f"[OpenAIProvider] Fallback model used: {model_choice} (primary={primary_model})")
                return response.choices[0].message.content.strip()
            except Exception as e:
                last_err = e
                # Attempt to classify error
                classification = "unknown"
                header_info = ""
                try:
                    # openai exceptions may have .response with headers
                    resp = getattr(e, 'response', None)
                    if resp is not None:
                        headers = getattr(resp, 'headers', {}) or {}
                        interesting = {k.lower(): v for k, v in headers.items() if k.lower().startswith('x-ratelimit') or 'quota' in k.lower()}
                        if interesting:
                            header_info = "; ".join(f"{k}={v}" for k, v in interesting.items())
                        if hasattr(resp, 'status_code'):
                            if resp.status_code == 429:
                                # Distinguish quota vs generic rate limit by message
                                msg = str(e).lower()
                                if 'insufficient_quota' in msg or 'quota' in msg:
                                    classification = 'quota'
                                else:
                                    classification = 'rate_limit'
                except Exception:
                    pass
                meta = f"model={model_choice} name={personality.name} classification={classification}"
                print(f"[OpenAIProvider] Error {meta} {header_info}: {e}")
                # If classification not quota/rate_limit or no fallback available, continue / raise later
                if classification not in {"quota", "rate_limit"}:
                    break
                # If quota error and we have a fallback model remaining, loop will try it
                continue
        meta = f"models_tried={attempted_models} name={personality.name}"
        raise Exception(f"OpenAI API error ({meta}): {last_err}")
    
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