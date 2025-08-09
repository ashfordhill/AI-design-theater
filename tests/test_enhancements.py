"""Tests for new enhancement features: keyword bias and convergence detection."""

from src.idea_generation.topic_generator import TopicGenerator
from src.conversation.conversation_manager import ConversationManager
from src.personalities.default_personalities import get_dreamer_personality, get_cost_cutter_personality
from src.models import ConversationConfig, ConversationMessage, MessageRole, ConversationSession
from src.personalities import PersonalityManager


def test_keyword_bias_no_crash(monkeypatch):
    monkeypatch.setenv("IDEA_KEYWORDS", "cache,edge")
    tg = TopicGenerator()
    topic = tg.get_random_topic()
    assert isinstance(topic, dict)
    assert "topic" in topic


def test_convergence_detection():
    pm = PersonalityManager(openai_api_key="dummy", anthropic_api_key="dummy")
    cm = ConversationManager(pm)
    config = ConversationConfig(topic="Test", max_turns=5, max_duration_minutes=1)
    session = ConversationSession(id="x", config=config, participants=[get_dreamer_personality(), get_cost_cutter_personality()])
    # Seed messages including FINAL DESIGN
    session.messages.append(ConversationMessage(role=MessageRole.ASSISTANT, content="Some discussion", speaker="Dreamer"))
    session.messages.append(ConversationMessage(role=MessageRole.ASSISTANT, content="FINAL DESIGN: summary", speaker="Cost Cutter"))
    assert cm._is_conversation_complete(session) is True
