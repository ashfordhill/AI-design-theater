"""Project storage and file management."""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..models import ConversationSession, DesignDocument


class ProjectStorage:
    """Manages storage of conversation sessions and design documents."""
    
    def __init__(self, base_dir: str = "projects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def save_session(self, session: ConversationSession) -> str:
        """Save a conversation session to disk."""
        # Create project directory
        project_name = self._sanitize_filename(session.config.topic)
        timestamp = session.started_at.strftime("%Y%m%d_%H%M%S")
        project_dir = self.base_dir / f"{timestamp}_{project_name}"
        project_dir.mkdir(exist_ok=True)
        
        # Save session data
        session_file = project_dir / "session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.dict(), f, indent=2, default=str)
        
        # Save conversation transcript
        transcript_file = project_dir / "conversation.md"
        self._save_conversation_transcript(session, transcript_file)
        
        return str(project_dir)
    
    def save_design_document(self, design_doc: DesignDocument, project_dir: str) -> str:
        """Save a design document to the project directory."""
        project_path = Path(project_dir)
        
        # Save design document JSON
        design_file = project_path / "design_document.json"
        with open(design_file, 'w', encoding='utf-8') as f:
            json.dump(design_doc.dict(), f, indent=2, default=str)
        
        # Save design document markdown
        md_file = project_path / "DESIGN.md"
        self._save_design_markdown(design_doc, md_file)
        
        # Save Mermaid diagram if present
        if design_doc.mermaid_diagram:
            mermaid_file = project_path / "diagram.mmd"
            with open(mermaid_file, 'w', encoding='utf-8') as f:
                f.write(design_doc.mermaid_diagram)
            # Attempt PNG rendering (optional)
            try:
                # Use mermaid-cli if available to produce SVG and PNG
                subprocess.run([
                    'mmdc', '-i', str(mermaid_file), '-o', str(project_path / 'diagram.svg'), '--quiet'
                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([
                    'mmdc', '-i', str(mermaid_file), '-o', str(project_path / 'diagram.png'), '--quiet'
                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        
        return str(md_file)
    
    def _save_conversation_transcript(self, session: ConversationSession, file_path: Path):
        """Save conversation as a readable markdown transcript."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Conversation Transcript\n\n")
            f.write(f"**Topic:** {session.config.topic}\n\n")
            # Include provider/model metadata
            participant_meta = []
            for p in session.participants:
                participant_meta.append(f"{p.name} ({p.provider.value}: {p.model})")
            f.write(f"**Participants:** {', '.join(participant_meta)}\n\n")
            f.write(f"**Started:** {session.started_at}\n\n")
            f.write(f"**Status:** {session.status}\n\n")
            if session.error_message:
                f.write(f"**Error:** {session.error_message}\n\n")
            
            if session.config.context:
                f.write(f"**Context:** {session.config.context}\n\n")
            
            f.write("---\n\n")
            
            # Build quick lookup for speaker metadata
            meta_lookup = {p.name: f"{p.provider.value}: {p.model}" for p in session.participants}
            for message in session.messages:
                if message.role.value == "assistant" and message.speaker:
                    suffix = f" ({meta_lookup.get(message.speaker, '')})" if message.speaker in meta_lookup else ""
                    f.write(f"## {message.speaker}{suffix}\n\n")
                    f.write(f"{message.content}\n\n")
                elif message.role.value == "user" and message.speaker == "system":
                    f.write(f"## System Prompt\n\n")
                    f.write(f"{message.content}\n\n")
    
    def _save_design_markdown(self, design_doc: DesignDocument, file_path: Path):
        """Save design document as formatted markdown."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {design_doc.title}\n\n")
            f.write(f"**Created:** {design_doc.created_at}\n\n")
            # Try to enrich participant data by reading sibling session.json
            enriched = []
            session_json = file_path.parent / 'session.json'
            if session_json.exists():
                try:
                    with open(session_json, 'r', encoding='utf-8') as sf:
                        data = json.load(sf)
                        for p in data.get('participants', []):
                            name = p.get('name')
                            provider = p.get('provider')
                            model = p.get('model')
                            if name and provider and model:
                                enriched.append(f"{name} ({provider}: {model})")
                except Exception:
                    pass
            if not enriched:
                enriched = design_doc.participants
            f.write(f"**Participants:** {', '.join(enriched)}\n\n")
            
            f.write("## Description\n\n")
            f.write(f"{design_doc.description}\n\n")
            
            if design_doc.key_decisions:
                f.write("## Key Decisions\n\n")
                for decision in design_doc.key_decisions:
                    f.write(f"- {decision}\n")
                f.write("\n")
            
            if design_doc.trade_offs:
                f.write("## Trade-offs\n\n")
                for tradeoff in design_doc.trade_offs:
                    f.write(f"- {tradeoff}\n")
                f.write("\n")
            
            if design_doc.implementation_notes:
                f.write("## Implementation Notes\n\n")
                for note in design_doc.implementation_notes:
                    f.write(f"- {note}\n")
                f.write("\n")
            
            if design_doc.mermaid_diagram:
                f.write("## Architecture Diagram\n\n")
                f.write("```mermaid\n")
                f.write(design_doc.mermaid_diagram)
                f.write("\n```\n\n")
            
            f.write("## Conversation Summary\n\n")
            f.write(f"{design_doc.conversation_summary}\n")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be safe for use as a filename."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length and clean up
        filename = filename.strip()[:50]
        filename = '_'.join(filename.split())  # Replace spaces with underscores
        
        return filename or "untitled_project"
    
    def list_projects(self) -> list:
        """List all saved projects."""
        projects = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                session_file = item / "session.json"
                if session_file.exists():
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        projects.append({
                            'path': str(item),
                            'name': item.name,
                            'topic': session_data.get('config', {}).get('topic', 'Unknown'),
                            'created': session_data.get('started_at', 'Unknown')
                        })
                    except Exception:
                        continue
        
        return sorted(projects, key=lambda x: x['created'], reverse=True)