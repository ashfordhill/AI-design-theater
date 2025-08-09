"""Developer test script to exercise collaborative conversation logic without real API keys.

Runs an 8-turn conversation using a dummy personality manager that fabricates
responses based on injected system guidance and attempts to cover new facets.

Usage:
  python scripts/dev_test_conversation.py
"""
from __future__ import annotations
import asyncio
import random
from datetime import datetime

import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models import (
    ConversationConfig,
    PersonalityConfig,
    LLMProvider,
    ConversationMessage,
    MessageRole,
    ConversationSession,
)
from src.conversation.conversation_manager import ConversationManager

FACET_KEYWORDS = {
    'storage': ['Postgres', 'S3 bucket'],
    'security': ['JWT auth', 'KMS encryption'],
    'scalability': ['autoscaling nodes', 'sharding'],
    'observability': ['central logging', 'metrics pipeline'],
    'deployment': ['CI/CD workflow', 'Terraform'],
    'api': ['REST gateway', 'GraphQL facade'],
    'data': ['event stream', 'schema evolution'],
}

ALL_FACETS = list(FACET_KEYWORDS.keys())

class DummyPersonalityManager:
    """Minimal stand‑in for PersonalityManager that returns synthetic replies."""
    def __init__(self):
        pass

    async def generate_response(self, personality, messages, context=None):
        # Find last system guidance
        guidance = ''
        for msg in reversed(messages):
            if msg.role == MessageRole.USER and msg.speaker == 'system' and msg.content.startswith('Guidance:'):
                guidance = msg.content
                break
        covered_facets = set()
        for msg in messages:
            if msg.role == MessageRole.ASSISTANT:
                for f in ALL_FACETS:
                    if f in msg.content.lower():
                        covered_facets.add(f)
        remaining = [f for f in ALL_FACETS if f not in covered_facets]
        if remaining:
            pick = remaining[0]
            facet_detail = ', '.join(FACET_KEYWORDS[pick][:2])
            facet_line = f"Facet {pick.title()}: {facet_detail}."
        else:
            facet_line = "Consolidating prior facets into coherent architecture."        
        # Decide whether to emit FINAL DESIGN
        assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]
        emit_final = len(assistant_msgs) >= 6 and remaining == [] and 'final design' not in messages[-1].content.lower()
        closing = ''
        if emit_final:
            closing = ('\nFINAL DESIGN:\n- Components: API, Worker, DB, Cache\n- Data: Postgres + S3 + Stream\n- Security: IAM, JWT, KMS\n- Ops: Observability stack + CI/CD')
        # Slight tone variation
        tone_prefix = 'Hey,' if 'casual' in (personality.system_prompt.lower()) else 'Note:'
        return f"{tone_prefix} {facet_line} {('[Ack] ' + guidance.split(':',1)[1].strip()) if guidance else ''}{closing}"

async def main():
    pm = DummyPersonalityManager()
    cm = ConversationManager(pm)  # type: ignore
    config = ConversationConfig(topic='Dev test collaborative design', max_turns=12, max_duration_minutes=5, tone='casual')
    dreamer = PersonalityConfig(name='Dreamer', provider=LLMProvider.ANTHROPIC, model='dummy-dreamer', system_prompt='Casual innovative persona (casual)')
    cutter = PersonalityConfig(name='Cost Cutter', provider=LLMProvider.OPENAI, model='dummy-cutter', system_prompt='Casual pragmatic persona (casual)')
    session = await cm.start_conversation(config, [dreamer, cutter])
    session = await cm.run_conversation(session)

    print(f"Status: {session.status}")
    print(f"Facets covered: {sorted(list(session.metadata.get('facets', [])))}")
    print(f"Decisions extracted: {len(session.metadata.get('decisions', []))}")
    print(f"Messages (assistant turns):")
    for m in session.messages:
        if m.role == MessageRole.ASSISTANT:
            print(f"[{m.speaker}] {m.content[:120].replace('\n',' ')}{'...' if len(m.content)>120 else ''}")

if __name__ == '__main__':
    asyncio.run(main())
