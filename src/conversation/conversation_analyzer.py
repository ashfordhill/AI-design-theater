"""Analyzes conversations to extract design insights."""

import re
from typing import List, Dict, Any
from ..models import ConversationSession, DesignDocument, MessageRole


class ConversationAnalyzer:
    """Analyzes conversation content to extract design insights."""
    
    def extract_design_document(self, session: ConversationSession) -> DesignDocument:
        """Extract a design document from the conversation."""
        messages = [m for m in session.messages if m.role == MessageRole.ASSISTANT]
        
        # Extract key information
        title = self._extract_title(session)
        description = self._extract_description(messages)
        if session.status == "error":
            description = (
                "Conversation aborted due to an error before completion. Partial ideas captured. "
                + (session.error_message or "")
            )
        key_decisions = self._extract_key_decisions(messages)
        trade_offs = self._extract_trade_offs(messages)
        implementation_notes = self._extract_implementation_notes(messages)
        
        return DesignDocument(
            title=title,
            description=description,
            conversation_id=session.id,
            participants=[p.name for p in session.participants],
            key_decisions=key_decisions,
            trade_offs=trade_offs,
            implementation_notes=implementation_notes,
            conversation_summary=self._create_conversation_summary(session)
        )
    
    def _extract_title(self, session: ConversationSession) -> str:
        """Extract or generate a title for the design."""
        topic = session.config.topic
        
        # Clean up the topic to make it a good title
        title = topic.strip()
        if not title.endswith(('.', '!', '?')):
            title = f"Design for {title}"
        
        return title
    
    def _extract_description(self, messages: List) -> str:
        """Extract a description from the conversation."""
        # Look for summary or description patterns
        description_patterns = [
            r"(?:the|our|this) (?:solution|approach|design|system) (?:is|will be|involves) (.+?)(?:\.|$)",
            r"(?:we|i) (?:propose|suggest|recommend) (.+?)(?:\.|$)",
            r"(?:the|our) (?:main|core|key) (?:idea|concept|approach) (?:is|involves) (.+?)(?:\.|$)"
        ]
        
        descriptions = []
        for message in messages:
            content = message.content.lower()
            for pattern in description_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                descriptions.extend(matches)
        
        if descriptions:
            # Take the longest description
            return max(descriptions, key=len).strip()
        
        # Fallback: use first substantial message
        for message in messages:
            if len(message.content) > 100:
                return message.content[:200] + "..."
        
        return "Design discussion between AI personalities"
    
    def _extract_key_decisions(self, messages: List) -> List[str]:
        """Extract key decisions made during the conversation."""
        decision_patterns = [
            r"(?:we|i) (?:decided|choose|selected|agreed) (?:to|on) (.+?)(?:\.|$)",
            r"(?:the|our) (?:decision|choice) (?:is|was) (?:to) (.+?)(?:\.|$)",
            r"(?:let's|we'll) (?:go with|use|implement) (.+?)(?:\.|$)"
        ]
        
        decisions = []
        for message in messages:
            content = message.content
            for pattern in decision_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                decisions.extend([match.strip() for match in matches])
        
        # Remove duplicates and clean up
        unique_decisions = []
        for decision in decisions:
            if decision and len(decision) > 10 and decision not in unique_decisions:
                unique_decisions.append(decision)
        
        return unique_decisions[:10]  # Limit to top 10
    
    def _extract_trade_offs(self, messages: List) -> List[str]:
        """Extract trade-offs discussed in the conversation."""
        tradeoff_patterns = [
            r"(?:trade.?off|compromise) (?:is|between|of) (.+?)(?:\.|$)",
            r"(?:however|but|although) (.+?) (?:we|this) (.+?)(?:\.|$)",
            r"(?:the|a) (?:downside|disadvantage|cost) (?:is|of) (.+?)(?:\.|$)",
            r"(?:on the other hand|alternatively) (.+?)(?:\.|$)"
        ]
        
        tradeoffs = []
        for message in messages:
            content = message.content
            for pattern in tradeoff_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if isinstance(matches[0], tuple) if matches else False:
                    tradeoffs.extend([' '.join(match) for match in matches])
                else:
                    tradeoffs.extend([match.strip() for match in matches])
        
        # Clean up and deduplicate
        unique_tradeoffs = []
        for tradeoff in tradeoffs:
            if tradeoff and len(tradeoff) > 15 and tradeoff not in unique_tradeoffs:
                unique_tradeoffs.append(tradeoff)
        
        return unique_tradeoffs[:8]  # Limit to top 8
    
    def _extract_implementation_notes(self, messages: List) -> List[str]:
        """Extract implementation-related notes."""
        implementation_patterns = [
            r"(?:to implement|implementation|we need to|we should) (.+?)(?:\.|$)",
            r"(?:the|our) (?:approach|method|way) (?:is|will be) (?:to) (.+?)(?:\.|$)",
            r"(?:first|next|then|finally) (?:we|step) (.+?)(?:\.|$)"
        ]
        
        notes = []
        for message in messages:
            content = message.content
            for pattern in implementation_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                notes.extend([match.strip() for match in matches])
        
        # Clean up and deduplicate
        unique_notes = []
        for note in notes:
            if note and len(note) > 10 and note not in unique_notes:
                unique_notes.append(note)
        
        return unique_notes[:12]  # Limit to top 12
    
    def _create_conversation_summary(self, session: ConversationSession) -> str:
        """Create a summary of the conversation flow."""
        assistant_messages = [m for m in session.messages if m.role == MessageRole.ASSISTANT]
        
        if not assistant_messages:
            return "No substantial conversation took place."
        
        summary = f"A {len(assistant_messages)}-turn conversation between "
        summary += f"{' and '.join([p.name for p in session.participants])} "
        summary += f"discussing '{session.config.topic}'. "
        
        if session.status == "completed":
            summary += "The conversation reached a natural conclusion with agreed-upon design decisions."
        elif session.status == "timeout":
            summary += "The conversation was concluded due to time limits."
        elif session.status == "max_turns_reached":
            summary += "The conversation reached the maximum number of turns."
        elif session.status == "error":
            summary += f"The conversation terminated early due to an error: {session.error_message}."
        elif session.status == "incomplete":
            summary += "The conversation ended without a FINAL DESIGN section."
        
        return summary