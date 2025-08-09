"""Run the daily design workflow locally (simulates GitHub Actions steps).

Usage (PowerShell):

  # Random mode with optional keywords
  $env:OPENAI_API_KEY='...'  # optional
  $env:ANTHROPIC_API_KEY='...'  # optional
  python scripts/run_daily_local.py --mode random --keywords cache,edge

  # Daily deterministic topic
  python scripts/run_daily_local.py --mode daily

  # Explicit topic
  python scripts/run_daily_local.py --topic "Design a feature flag system" --context "Focus on multi-tenant rollout safety"

The script will:
  1. Resolve topic (manual > provided topic arg > mode daily/random)
  2. Run design session
  3. Update README and PROJECTS_INDEX via update_docs.py
  4. Print resulting project directory

Environment variables respected:
  IDEA_KEYWORDS  - baseline keyword bias
  OPENAI_API_KEY / ANTHROPIC_API_KEY - provider keys
  OPENAI_FALLBACK_MODEL - fallback OpenAI model if primary hits quota/rate limit
"""
from __future__ import annotations

import argparse
import os
import sys
import asyncio
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.idea_generation.topic_generator import TopicGenerator  # noqa: E402
from src.main import AIDesignTheater  # noqa: E402


def resolve_topic(args) -> tuple[str, str | None]:
    if args.topic:
        return args.topic, args.context
    tg = TopicGenerator()
    mode = (args.mode or 'daily').lower()
    if mode == 'random':
        if args.keywords:
            os.environ['IDEA_KEYWORDS'] = args.keywords
        data = tg.get_random_topic()
    else:
        if args.keywords:
            os.environ['IDEA_KEYWORDS'] = args.keywords
        data = tg.get_daily_topic()
    return data['topic'], data.get('context')


def parse_args():
    p = argparse.ArgumentParser(description='Run local daily design workflow simulation.')
    p.add_argument('--mode', choices=['daily', 'random'], default='daily', help='Topic selection mode when --topic not provided')
    p.add_argument('--topic', help='Explicit topic (overrides mode)')
    p.add_argument('--context', help='Optional context string')
    p.add_argument('--keywords', help='Comma separated keywords to bias selection (temporarily overrides IDEA_KEYWORDS)')
    p.add_argument('--max-turns', type=int, help='Override max turns for this run')
    p.add_argument('--max-duration', type=int, help='Override max duration minutes for this run')
    p.add_argument('--simulate', action='store_true', help='Simulate without real LLM calls (no API keys required)')
    return p.parse_args()


def run_update_docs():
    update_script = ROOT / 'scripts' / 'update_docs.py'
    if update_script.exists():
        exit_code = os.system(f"{sys.executable} {update_script}")
        if exit_code != 0:
            print('[warn] update_docs.py exited with non-zero status')
    else:
        print('[warn] update_docs.py not found; skipping docs update')


def main():
    args = parse_args()
    topic, context = resolve_topic(args)
    print(f"[topic] {topic}")
    if context:
        print(f"[context] {context}")

    if args.simulate:
        # Fabricate a minimal session + design doc without external API calls
        from src.models import ConversationConfig, ConversationSession, PersonalityConfig, LLMProvider, ConversationMessage, MessageRole, DesignDocument
        from src.conversation import ConversationAnalyzer
        from src.diagram_generation import MermaidGenerator
        from src.storage import ProjectStorage
        import uuid
        import datetime as _dt

        conv_config = ConversationConfig(topic=topic, context=context or "")
        dreamer = PersonalityConfig(name='Dreamer', provider=LLMProvider.ANTHROPIC, model='sim-anthropic', system_prompt='Simulated dreamer')
        cutter = PersonalityConfig(name='Cost Cutter', provider=LLMProvider.OPENAI, model='sim-openai', system_prompt='Simulated cost cutter')
        session = ConversationSession(
            id=str(uuid.uuid4()),
            config=conv_config,
            participants=[dreamer, cutter],
            started_at=_dt.datetime.now()
        )
        # Add system prompt and two assistant exchanges including FINAL DESIGN
        session.messages.append(ConversationMessage(role=MessageRole.USER, content=f"Let's design: {topic}\n\n{context or ''}", speaker='system'))
        session.messages.append(ConversationMessage(role=MessageRole.ASSISTANT, content="Initial exploration of high-level architecture, constraints, and goals.", speaker='Dreamer'))
        session.messages.append(ConversationMessage(role=MessageRole.ASSISTANT, content="Refined pragmatic view with trade-offs. FINAL DESIGN: Components, data flow, storage choices, and security layers.", speaker='Cost Cutter'))
        session.status = 'completed'
        session.ended_at = _dt.datetime.now()

        analyzer = ConversationAnalyzer()
        design_doc = analyzer.extract_design_document(session)
        mg = MermaidGenerator()
        design_doc.mermaid_diagram = mg.generate_architecture_diagram(design_doc)
        session.design_document = design_doc
        storage = ProjectStorage()
        project_dir = storage.save_session(session)
        storage.save_design_document(design_doc, project_dir)
    else:
        async def run():
            theater = AIDesignTheater()
            project_dir = await theater.run_design_session(
                topic=topic,
                context=context,
                max_turns=args.max_turns,
                max_duration_minutes=args.max_duration,
            )
            return project_dir
        project_dir = asyncio.run(run())
    run_update_docs()
    print(f"[result] project_dir={project_dir}")

    # Summarize outputs
    print('\nArtifacts:')
    for name in ["session.json", "DESIGN.md", "conversation.md", "diagram.mmd", "diagram.svg", "diagram.png"]:
        p = Path(project_dir) / name
        if p.exists():
            print(f"  ✔ {name}")
        else:
            print(f"  ✖ {name}")


if __name__ == '__main__':
    main()
