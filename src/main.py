"""Main application orchestrator for AI Design Theater."""

import asyncio
from typing import Optional
from .config import config
from .models import ConversationConfig
from .personalities import PersonalityManager, get_idealist_personality, get_cost_cutter_personality
from .conversation import ConversationManager, ConversationAnalyzer
from .diagram_generation import MermaidGenerator
from .storage import ProjectStorage


class AIDesignTheater:
    """Main application class that orchestrates AI design conversations."""
    
    def __init__(self):
        self.personality_manager = PersonalityManager(
            openai_api_key=config.openai_api_key,
            anthropic_api_key=config.anthropic_api_key
        )
        self.conversation_manager = ConversationManager(self.personality_manager)
        self.conversation_analyzer = ConversationAnalyzer()
        self.mermaid_generator = MermaidGenerator()
        self.storage = ProjectStorage(config.projects_dir)
    
    async def run_design_session(
        self,
        topic: str,
        context: Optional[str] = None,
        max_turns: Optional[int] = None,
    max_duration_minutes: Optional[int] = None,
    tone: Optional[str] = None,
    debate_intensity: Optional[int] = None,
    diagram_detail_level: Optional[int] = None
    ) -> str:
        """Run a complete design session and return the project directory path."""
        
        # Validate API keys
        if not config.validate_api_keys():
            raise ValueError("No API keys configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        
        # Create conversation configuration
        conv_config = ConversationConfig(
            topic=topic,
            context=context,
            max_turns=max_turns or config.default_max_turns,
            max_duration_minutes=max_duration_minutes or config.default_max_duration_minutes,
            tone=tone,
            debate_intensity=debate_intensity if debate_intensity is not None else config.default_debate_intensity,
            diagram_detail_level=diagram_detail_level if diagram_detail_level is not None else config.default_diagram_detail_level
        )
        
        # Get personalities
        idealist = get_idealist_personality()
        cost_cutter = get_cost_cutter_personality()
        personalities = [idealist, cost_cutter]
        
        # Validate personalities
        for personality in personalities:
            if not await self.personality_manager.validate_personality(personality):
                raise ValueError(f"Cannot connect to {personality.provider.value} for {personality.name}")
        
        print(f"🎭 Starting design conversation: {topic}")
        print(
            f"👥 Participants: {idealist.name} [{idealist.model}] & {cost_cutter.name} [{cost_cutter.model}]"
        )
        print(
            f"⚙️  Settings: turns≤{conv_config.max_turns}, duration≤{conv_config.max_duration_minutes}m, "
            f"debate_intensity={conv_config.debate_intensity}, diagram_detail={conv_config.diagram_detail_level}"
        )
        
        # Start and run conversation
        session = await self.conversation_manager.start_conversation(
            conv_config, personalities
        )
        
        print("💬 Conversation in progress...")
        session = await self.conversation_manager.run_conversation(session)
        
        print(f"✅ Conversation completed with status: {session.status}")
        print(f"📊 Total messages: {len([m for m in session.messages if m.role.value == 'assistant'])}")
        
        # Analyze conversation and generate design document
        print("📝 Analyzing conversation and generating design document...")
        design_doc = self.conversation_analyzer.extract_design_document(session)
        # Integrate enriched metadata if present (decisions, tradeoffs, notes)
        md = session.metadata or {}
        if md.get('decisions') and not design_doc.key_decisions:
            design_doc.key_decisions = md['decisions'][:10]
        if md.get('tradeoffs') and not design_doc.trade_offs:
            design_doc.trade_offs = md['tradeoffs'][:8]
        if md.get('implementation_notes'):
            # Merge unique
            existing = set(design_doc.implementation_notes)
            for n in md['implementation_notes']:
                if n not in existing:
                    design_doc.implementation_notes.append(n)
                    existing.add(n)
        
        # Generate Mermaid diagram
        print("📊 Generating architecture diagram...")
        design_doc.mermaid_diagram = self.mermaid_generator.generate_architecture_diagram(
            design_doc, detail_level=conv_config.diagram_detail_level
        )
        
        # Save everything
        print("💾 Saving project files...")
        project_dir = self.storage.save_session(session)
        self.storage.save_design_document(design_doc, project_dir)
        
        print(f"🎉 Design session complete! Project saved to: {project_dir}")
        
        return project_dir
    
    def list_projects(self) -> list:
        """List all saved design projects."""
        return self.storage.list_projects()
    
    async def validate_setup(self) -> dict:
        """Validate that the application is properly configured."""
        results = {
            "api_keys": config.validate_api_keys(),
            "openai_connection": False,
            "anthropic_connection": False,
            "projects_dir": self.storage.base_dir.exists(),
        }

        # Validate provider connectivity only if keys present
        try:
            if config.openai_api_key:
                openai_personality = get_cost_cutter_personality()
                results["openai_connection"] = await self.personality_manager.validate_personality(openai_personality)
        except Exception:
            results["openai_connection"] = False

        try:
            if config.anthropic_api_key:
                anthropic_personality = get_idealist_personality()
                results["anthropic_connection"] = await self.personality_manager.validate_personality(anthropic_personality)
        except Exception:
            results["anthropic_connection"] = False

        return results


# Convenience function for direct usage
async def run_design_session(topic: str, context: Optional[str] = None) -> str:
    """Convenience function to run a design session."""
    theater = AIDesignTheater()
    return await theater.run_design_session(topic, context)