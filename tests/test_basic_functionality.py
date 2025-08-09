"""Basic functionality tests for AI Design Theater."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.models import PersonalityConfig, LLMProvider, ConversationConfig
from src.personalities import get_dreamer_personality, get_cost_cutter_personality
from src.conversation import ConversationAnalyzer
from src.diagram_generation import MermaidGenerator


def test_personality_configurations():
    """Test that default personalities are properly configured."""
    dreamer = get_dreamer_personality()
    cost_cutter = get_cost_cutter_personality()
    
    assert dreamer.name == "Dreamer"
    assert cost_cutter.name == "Cost Cutter"
    assert dreamer.provider == LLMProvider.ANTHROPIC
    assert cost_cutter.provider == LLMProvider.OPENAI
    assert dreamer.temperature > cost_cutter.temperature  # Dreamer should be more creative


def test_conversation_config():
    """Test conversation configuration validation."""
    config = ConversationConfig(
        topic="Test design",
        max_turns=10,
        max_duration_minutes=15
    )
    
    assert config.topic == "Test design"
    assert config.max_turns == 10
    assert config.max_duration_minutes == 15


def test_mermaid_generator():
    """Test Mermaid diagram generation."""
    from src.models import DesignDocument
    
    design_doc = DesignDocument(
        title="Test Design",
        description="A test design for validation",
        conversation_id="test-123",
        participants=["Dreamer", "Cost Cutter"],
        key_decisions=["Use microservices", "Implement caching"],
        implementation_notes=["First deploy API", "Then add frontend", "Finally optimize"]
    )
    
    generator = MermaidGenerator()
    diagram = generator.generate_architecture_diagram(design_doc)
    
    assert diagram.startswith("flowchart TD") or diagram.startswith("graph TD") or diagram.startswith("sequenceDiagram")
    assert len(diagram) > 50  # Should generate substantial content


def test_conversation_analyzer():
    """Test conversation analysis and design document extraction."""
    from src.models import ConversationSession, ConversationMessage, MessageRole
    
    # Create mock session
    session = ConversationSession(
        id="test-session",
        config=ConversationConfig(topic="Test API Design"),
        participants=[get_dreamer_personality(), get_cost_cutter_personality()]
    )
    
    # Add mock messages
    session.messages = [
        ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="I think we should use GraphQL for this API design. It offers great flexibility.",
            speaker="Dreamer"
        ),
        ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="While GraphQL is nice, REST is simpler and more widely understood. Let's go with REST.",
            speaker="Cost Cutter"
        ),
        ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="Good point. We decided to use REST API with proper versioning.",
            speaker="Dreamer"
        )
    ]
    
    analyzer = ConversationAnalyzer()
    design_doc = analyzer.extract_design_document(session)
    
    assert design_doc.title == "Design for Test API Design"
    assert len(design_doc.participants) == 2
    assert "Dreamer" in design_doc.participants
    assert "Cost Cutter" in design_doc.participants


if __name__ == "__main__":
    pytest.main([__file__])