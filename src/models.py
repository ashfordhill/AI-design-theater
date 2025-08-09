"""Core data models for the AI Design Theater."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    # Future: LOCAL = "local"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):
    """A single message in the conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    speaker: Optional[str] = None  # Which personality spoke
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PersonalityConfig(BaseModel):
    """Configuration for an AI personality."""
    name: str
    provider: LLMProvider
    model: str
    system_prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    personality_traits: Dict[str, Any] = Field(default_factory=dict)


class ConversationConfig(BaseModel):
    """Configuration for a conversation session."""
    max_turns: int = Field(default=20, ge=1)
    max_duration_minutes: int = Field(default=30, ge=1)
    topic: str
    context: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    tone: Optional[str] = Field(default=None, description="Stylistic tone guidance (e.g., 'casual')")
    debate_intensity: int = Field(default=5, ge=0, le=10, description="Higher => more disagreement & challenge.")
    diagram_detail_level: int = Field(default=5, ge=1, le=10, description="Controls richness of generated diagrams.")


class DesignDocument(BaseModel):
    """Generated design document."""
    title: str
    description: str
    conversation_id: str
    participants: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    mermaid_diagram: Optional[str] = None
    key_decisions: List[str] = Field(default_factory=list)
    trade_offs: List[str] = Field(default_factory=list)
    implementation_notes: List[str] = Field(default_factory=list)
    conversation_summary: str = ""


class ConversationSession(BaseModel):
    """A complete conversation session."""
    id: str
    config: ConversationConfig
    participants: List[PersonalityConfig]
    messages: List[ConversationMessage] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    design_document: Optional[DesignDocument] = None
    status: str = "active"  # active, completed, timeout, error
    error_message: Optional[str] = None  # captured error detail if status=error
    metadata: Dict[str, Any] = Field(default_factory=dict)  # runtime accumulation (facets, decisions, etc.)