"""Main conversation orchestration logic."""

import asyncio
import uuid
import traceback
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from ..models import (
    ConversationSession, ConversationConfig, ConversationMessage, 
    PersonalityConfig, MessageRole, LLMProvider
)
from ..personalities import PersonalityManager
from ..personalities.stance_memory import StanceMemoryManager


class ConversationManager:
    """Manages AI-to-AI conversations."""
    
    def __init__(self, personality_manager: PersonalityManager):
        self.personality_manager = personality_manager
        # Persistent stance memory across sessions
        self.stance_memory = StanceMemoryManager()
    
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
        session.metadata.setdefault('facets', set())
        session.metadata.setdefault('decisions', [])
        session.metadata.setdefault('tradeoffs', [])
        session.metadata.setdefault('implementation_notes', [])
        session.metadata.setdefault('shadow_mode', False)
        min_facets_for_final = 4
        min_turns_for_final = 6

        while (
            turn_count < session.config.max_turns and
            datetime.now() - start_time < max_duration and
            not self._is_conversation_complete(session)
        ):
            current_personality = session.participants[current_speaker_idx]
            
            try:
                # Build dynamic collaboration guidance
                guidance = self._build_turn_guidance(session, current_speaker_idx, turn_count)
                if guidance:
                    session.messages.append(ConversationMessage(
                        role=MessageRole.USER,
                        content=guidance,
                        speaker="system"
                    ))

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
                
                # Add response to conversation (apply redundancy nudge)
                message = ConversationMessage(
                    role=MessageRole.ASSISTANT,
                    content=response,
                    speaker=current_personality.name
                )
                session.messages.append(message)

                self._update_facets_and_metadata(session, message)
                # Feed stance memory with the latest assistant utterance
                try:
                    self.stance_memory.analyze_and_update_counts(
                        current_personality.name, [message.content]
                    )
                except Exception:
                    pass

                # Gate premature FINAL DESIGN: if model outputs it too early and criteria not met, convert to normal discussion
                if self._contains_final_design(message.content):
                    if not self._final_design_allowed(session, turn_count, min_turns_for_final, min_facets_for_final):
                        message.content = re.sub(r'(?i)FINAL DESIGN:?','(Continuing exploration – FINAL DESIGN later)', message.content)

                
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
                    # Attempt cross-provider fallback before disabling speaker
                    other_idx = 1 - current_speaker_idx
                    if self._attempt_provider_fallback(session, failing_idx=current_speaker_idx, other_idx=other_idx, error_text=err_text):
                        # Successfully swapped provider for failing personality; retry loop (do not increment turn)
                        continue
                    # If fallback not possible, degrade to shadow mode as before
                    disabled_speakers.add(current_speaker_idx)
                    session.error_message = (session.error_message or "") + f"\nDisabled {current_personality.name} due to quota exhaustion: {err_text}"
                    remaining_idx = other_idx
                    if remaining_idx not in disabled_speakers:
                        session.metadata['shadow_mode'] = True
                        session.messages.append(ConversationMessage(
                            role=MessageRole.USER,
                            content=(
                                f"System notice: {current_personality.name} is unavailable (quota). "
                                f"{session.participants[remaining_idx].name}, continue the architectural debate by also "
                                "representing cost/pragmatic trade-offs. Aim to converge and provide a FINAL DESIGN section."),
                            speaker="system"
                        ))
                        current_speaker_idx = remaining_idx
                        continue
                    session.status = "error"
                    session.error_message = (session.error_message or "") + f"\nAll participants disabled (quota)."
                    break
                else:
                    # Try generic provider fallback first
                    other_idx = 1 - current_speaker_idx
                    if self._attempt_provider_fallback(session, failing_idx=current_speaker_idx, other_idx=other_idx, error_text=err_text):
                        continue  # retry loop with reassigned provider
                    session.status = "error"
                    session.error_message = f"{err_text}\n{tb}"
                    assistant_msgs = [m for m in session.messages if m.role == MessageRole.ASSISTANT]
                    if len(assistant_msgs) < 1 and len(session.participants) == 2:
                        try:
                            other_personality = session.participants[other_idx]
                            fallback = (
                                "Encountered an error generating a response from one participant (no fallback possible). "
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

    def _contains_final_design(self, content: str) -> bool:
        return 'final design' in content.lower()

    def _final_design_allowed(self, session: ConversationSession, turn_count: int, min_turns: int, min_facets: int) -> bool:
        facets = session.metadata.get('facets', set())
        if len(facets) < min_facets or turn_count < min_turns:
            return False
        return True

    def _build_turn_guidance(self, session: ConversationSession, speaker_idx: int, turn_index: int) -> str:
        """Construct a micro system hint to shape the next reply."""
        assistant_msgs = [m for m in session.messages if m.role == MessageRole.ASSISTANT]
        if not assistant_msgs:
            return "Briefly propose an initial architectural direction. End with a question inviting critique." if session.config.tone == 'casual' else "Outline an initial architectural approach and ask a clarifying question."
        last = assistant_msgs[-1]
        facets = session.metadata.get('facets', set())
        needed_facets = [f for f in ['storage','security','scalability','observability','data','api','deployment'] if f not in facets]
        prompt_bits = []
        # Encourage acknowledgement
        prompt_bits.append("Acknowledge one concrete prior point (briefly)")
        # Encourage covering missing facet
        if needed_facets:
            prompt_bits.append(f"Introduce or deepen: {needed_facets[0]}")
        # If shadow mode, emulate other perspective
        if session.metadata.get('shadow_mode'):
            prompt_bits.append("Also briefly simulate what the missing persona might challenge")
        # Debate intensity injection
        intensity = getattr(session.config, 'debate_intensity', 5)
        if intensity >= 7:
            prompt_bits.append("Directly challenge an assumption or risky choice just raised; propose an alternative")
        elif intensity >= 4:
            prompt_bits.append("Politely question a potential weakness or cost driver; suggest leaner option")
        else:
            prompt_bits.append("Maintain collaborative tone")
        # Question or convergence
        if self._has_final_design_block(session):
            return ""  # no extra guidance after final
        # Stance memory principle reinforcement occasionally
        principle = None
        try:
            speaker_name = session.participants[speaker_idx].name
            if turn_index % max(3, 8 - session.config.debate_intensity) == 0:
                principle = self.stance_memory.pick_principle(speaker_name, turn_index)
        except Exception:
            principle = None
        if principle:
            prompt_bits.append(f"Reassert one guiding principle briefly: '{principle}' (do not repeat every turn)")
        if len(assistant_msgs) < max(4, (session.config.max_turns//2)):
            prompt_bits.append("End with an open question")
        else:
            prompt_bits.append("If coverage feels sufficient, move toward drafting FINAL DESIGN soon")
        if session.config.tone == 'casual':
            prompt_bits.append("Keep tone conversational, a bit informal")
        return "Guidance: " + "; ".join(prompt_bits)

    def _update_facets_and_metadata(self, session: ConversationSession, message: ConversationMessage):
        text = message.content.lower()
        facets = session.metadata.get('facets', set())
        facet_map = {
            'storage': ['database','s3','store','schema','data lake','cache'],
            'security': ['encrypt','auth','iam','security','zero trust','acl','kms'],
            'scalability': ['scale','autoscale','throughput','latency','shard','partition'],
            'observability': ['logging','metrics','tracing','otel','monitor','alert'],
            'deployment': ['ci/cd','deploy','pipeline','terraform','infrastructure','iac'],
            'api': ['api','rest','graphql','endpoint','gateway'],
            'data': ['data model','schema','entity','event','stream']
        }
        for facet, keywords in facet_map.items():
            if any(k in text for k in keywords):
                facets.add(facet)
        session.metadata['facets'] = facets
        # Simple extraction rules
        if 'final design' in text:
            # Extract bullet/numbered style lines after final design
            lines = [l.strip('- *0123456789. ') for l in message.content.splitlines() if l.strip()]
            for l in lines:
                if len(l) < 8:
                    continue
                if any(w in l.lower() for w in ['use ','we will','choose','select','decid','architecture','component']):
                    self._append_unique(session.metadata['decisions'], l)
        # Implementation notes heuristics
        if any(w in text for w in ['first','then','next','finally']):
            snippet = message.content[:180]
            self._append_unique(session.metadata['implementation_notes'], snippet)
        # Trade-off simple detection
        if any(w in text for w in ['however','trade-off','tradeoff','but ','versus','vs.']):
            snippet = message.content[:180]
            self._append_unique(session.metadata['tradeoffs'], snippet)

    def _append_unique(self, lst, item):
        if item not in lst and len(lst) < 50:
            lst.append(item)

    # --- Provider fallback logic ---
    def _attempt_provider_fallback(self, session: ConversationSession, failing_idx: int, other_idx: int, error_text: str) -> bool:
        """Try to re-home a failing personality onto the surviving provider instead of disabling it.

        Returns True if fallback performed; False otherwise.
        """
        if other_idx < 0 or other_idx >= len(session.participants):
            return False
        failing = session.participants[failing_idx]
        other = session.participants[other_idx]
        # If already same provider, no cross-provider fallback possible
        if failing.provider == other.provider:
            return False
        # Only fallback if the *other* provider has not itself been marked disabled via prior quota errors
        # (We infer this by absence of its name in accumulated quota error messages.)
        existing_err = session.error_message or ""
        if other.name in existing_err and 'quota' in existing_err.lower():
            return False
        # Construct replacement PersonalityConfig with other.provider while retaining identity & traits
        replacement_model = self._fallback_model_for(failing.name, other.provider, other.model)
        try:
            new_config = PersonalityConfig(
                name=failing.name,
                provider=other.provider,
                model=replacement_model,
                system_prompt=failing.system_prompt + "\n(Operating via fallback provider due to prior quota error: " + failing.provider.value + ")",
                temperature=failing.temperature,
                max_tokens=failing.max_tokens,
                personality_traits=failing.personality_traits.copy()
            )
        except Exception:
            return False
        session.participants[failing_idx] = new_config
        # Log and inform conversation
        session.error_message = (session.error_message or "") + (
            f"\n{failing.name} provider quota error; switched to {other.provider.value} model={replacement_model} (fallback)"
        )
        session.messages.append(ConversationMessage(
            role=MessageRole.USER,
            content=(
                f"System notice: {failing.name} experienced a quota error using {failing.provider.value}. "
                f"It has been reassigned to the {other.provider.value} provider with model '{replacement_model}' while keeping its distinct role."),
            speaker="system"
        ))
        return True

    def _fallback_model_for(self, name: str, provider: LLMProvider, other_model: str) -> str:
        """Heuristic model selection to maintain some differentiation after fallback."""
        if provider == LLMProvider.ANTHROPIC:
            # Other participant already Anthropic. Use a lighter / different variant for distinction.
            if 'haiku' in other_model:
                return 'claude-3-5-sonnet-20240620'
            if 'sonnet' in other_model:
                return 'claude-3-haiku-20240307'
            return other_model  # unknown variant; reuse
        if provider == LLMProvider.OPENAI:
            # Choose a different gpt-4 family variant where possible
            if 'mini' in other_model.lower():
                return 'gpt-4o'
            return 'gpt-4o-mini'
        return other_model

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