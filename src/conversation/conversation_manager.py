"""Main conversation orchestration logic."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from ..models import (
    ConversationSession, ConversationConfig, ConversationMessage, 
    PersonalityConfig, MessageRole
)
from ..personalities import PersonalityManager


class ConversationManager:
    """Manages AI-to-AI conversations."""
    
    def __init__(self, personality_manager: PersonalityManager):
        self.personality_manager = personality_manager
    
    async def start_conversation(
        self,
        config: ConversationConfig,
        personalities: List[PersonalityConfig],
        initial_prompt: Optional[str] = None
    ) -> ConversationSession:
        """Start a new conversation session."""
        if len(personalities) != 2:
            raise ValueError("Exactly 2 personalities required for conversation")
        
        session = ConversationSession(
            id=str(uuid.uuid4()),
            config=config,
            participants=personalities
        )
        
        # Add initial system context if provided
        if initial_prompt:
            session.messages.append(ConversationMessage(
                role=MessageRole.USER,
                content=initial_prompt,
                speaker="system"
            ))
        
        return session
    
    async def run_conversation(self, session: ConversationSession) -> ConversationSession:
        """Run the complete conversation until completion."""
        start_time = datetime.now()
        max_duration = timedelta(minutes=session.config.max_duration_minutes)
        
        current_speaker_idx = 0  # Start with first personality
        turn_count = 0
        
        # Initial prompt to get the conversation started
        if not session.messages or session.messages[-1].role == MessageRole.USER:
            initial_message = self._create_initial_message(session.config)
            session.messages.append(initial_message)
        
        while (
            turn_count < session.config.max_turns and
            datetime.now() - start_time < max_duration and
            not self._is_conversation_complete(session)
        ):
            current_personality = session.participants[current_speaker_idx]
            
            try:
                # Generate response from current speaker
                response = await self.personality_manager.generate_response(
                    current_personality,
                    session.messages,
                    session.config.context
                )
                
                # Add response to conversation
                message = ConversationMessage(
                    role=MessageRole.ASSISTANT,
                    content=response,
                    speaker=current_personality.name
                )
                session.messages.append(message)
                
                # Inject convergence hint if nearing limits and no final design yet
                if (
                    turn_count >= max(2, session.config.max_turns - 3)
                    and not self._has_final_design_block(session)
                ):
                    session.messages.append(ConversationMessage(
                        role=MessageRole.USER,
                        content=(
                            "Please collaboratively converge now. Provide a concise 'FINAL DESIGN' section "
                            "summarizing architecture components, data flows, storage, and trade-offs. After that, stop."
                        ),
                        speaker="system"
                    ))

                # Switch to other speaker
                current_speaker_idx = 1 - current_speaker_idx
                turn_count += 1
                
                # Small delay to prevent rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                session.status = "error"
                print(f"Error in conversation: {e}")
                break
        
        # Determine final status
        if self._is_conversation_complete(session):
            session.status = "completed"
        elif datetime.now() - start_time >= max_duration:
            session.status = "timeout"
        elif turn_count >= session.config.max_turns:
            session.status = "max_turns_reached"
        
        session.ended_at = datetime.now()
        return session
    
    def _create_initial_message(self, config: ConversationConfig) -> ConversationMessage:
        """Create the initial message to start the conversation."""
        prompt = f"""Let's design a solution for: {config.topic}

Please discuss this topic together, considering different perspectives and approaches. 
Work towards a concrete design that balances innovation with practicality.

{config.context or ''}

Begin the discussion!"""
        
        return ConversationMessage(
            role=MessageRole.USER,
            content=prompt,
            speaker="system"
        )
    
    def _has_final_design_block(self, session: ConversationSession) -> bool:
        for msg in reversed(session.messages):
            if msg.role == MessageRole.ASSISTANT and "final design" in msg.content.lower():
                return True
        return False

    def _is_conversation_complete(self, session: ConversationSession) -> bool:
        """Check if the conversation has reached a natural conclusion."""
        # Allow early completion once at least 2 assistant messages exist
        assistant_msgs = [m for m in session.messages if m.role == MessageRole.ASSISTANT]
        if len(assistant_msgs) < 2:
            return False
        return self._has_final_design_block(session)
    
    def get_conversation_summary(self, session: ConversationSession) -> str:
        """Generate a summary of the conversation."""
        if not session.messages:
            return "No conversation took place."
        
        participant_names = [p.name for p in session.participants]
        message_count = len([m for m in session.messages if m.role == MessageRole.ASSISTANT])
        
        summary = f"Conversation between {' and '.join(participant_names)} "
        summary += f"about '{session.config.topic}'. "
        summary += f"Total messages: {message_count}, Status: {session.status}"
        
        return summary