"""Main conversation orchestration logic."""

import asyncio
import uuid
import traceback
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
        
        disabled_speakers = set()
        while (
            turn_count < session.config.max_turns and
            datetime.now() - start_time < max_duration and
            not self._is_conversation_complete(session)
        ):
            current_personality = session.participants[current_speaker_idx]
            
            try:
                # Generate response with basic retry
                response = None
                last_error = None
                for attempt in range(3):
                    try:
                        response = await self.personality_manager.generate_response(
                            current_personality,
                            session.messages,
                            session.config.context
                        )
                        break
                    except Exception as gen_err:
                        last_error = gen_err
                        await asyncio.sleep(1 + attempt)
                if response is None:
                    raise last_error or Exception("Unknown generation failure")
                
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
                err_text = str(e)
                lower_err = err_text.lower()
                tb = traceback.format_exc()
                print(f"Error in conversation: {e}\n{tb}")
                # Handle OpenAI insufficient quota gracefully: disable this speaker and let other continue solo
                if "insufficient_quota" in lower_err or "quota" in lower_err:
                    disabled_speakers.add(current_speaker_idx)
                    session.error_message = (session.error_message or "") + f"\nDisabled {current_personality.name} due to quota exhaustion: {err_text}"
                    # System instruction for remaining participant to emulate both roles
                    remaining_idx = 1 - current_speaker_idx
                    if remaining_idx not in disabled_speakers:
                        session.messages.append(ConversationMessage(
                            role=MessageRole.USER,
                            content=(
                                f"System notice: {current_personality.name} is unavailable (quota). "
                                f"{session.participants[remaining_idx].name}, continue the architectural debate by also "
                                "representing cost/pragmatic trade-offs. Aim to converge and provide a FINAL DESIGN section."),
                            speaker="system"
                        ))
                        # Switch permanently to remaining speaker
                        current_speaker_idx = remaining_idx
                        # Do not increment turn_count here (the next successful response will)
                        continue
                    else:
                        session.status = "error"
                        session.error_message = (session.error_message or "") + f"\nAll participants disabled (quota)."
                        break
                else:
                    session.status = "error"
                    session.error_message = f"{err_text}\n{tb}"
                    # Attempt at least one message from the other participant if none yet
                    assistant_msgs = [m for m in session.messages if m.role == MessageRole.ASSISTANT]
                    if len(assistant_msgs) < 1 and len(session.participants) == 2:
                        try:
                            other_idx = 1 - current_speaker_idx
                            other_personality = session.participants[other_idx]
                            fallback = (
                                "Encountered an error generating a response from the first participant. "
                                "Providing an initial perspective to allow partial artifacts. Error details were logged."
                            )
                            session.messages.append(ConversationMessage(
                                role=MessageRole.ASSISTANT,
                                content=fallback,
                                speaker=other_personality.name
                            ))
                        except Exception:
                            pass
                    break
        
        # Determine final status
        if self._is_conversation_complete(session):
            session.status = "completed"
        elif datetime.now() - start_time >= max_duration:
            session.status = "timeout"
        elif turn_count >= session.config.max_turns:
            session.status = "max_turns_reached"
        elif session.status != "error":
            # If not completed but also not flagged, mark as partial
            session.status = "incomplete"
        
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