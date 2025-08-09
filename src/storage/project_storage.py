"""Project storage and file management."""

import os
import json
import subprocess
import shutil
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
            self._render_mermaid_assets(mermaid_file, project_path)
        
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

    # --- Internal helpers ---
    def _render_mermaid_assets(self, mermaid_file: Path, project_path: Path):
        """Attempt to render Mermaid diagram to SVG and PNG with multiple strategies.

        Strategies (in order):
          1. MERMAID_CLI_COMMAND env override (e.g. "npx -y @mermaid-js/mermaid-cli")
          2. mmdc on PATH (global install)
          3. npx -y @mermaid-js/mermaid-cli
        Writes a log file diagram_render.log with details on failures.
        """
        log_file = project_path / 'diagram_render.log'
        attempts = []
        svg_out = project_path / 'diagram.svg'
        png_out = project_path / 'diagram.png'

        def run_cmd(cmd, label):
            attempts.append(label)
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
                success = proc.returncode == 0 and svg_out.exists()
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{label}] returncode={proc.returncode}\n")
                    lf.write(f"cmd: {' '.join(cmd)}\n")
                    if proc.stdout:
                        lf.write(f"stdout:\n{proc.stdout[:500]}\n")
                    if proc.stderr:
                        lf.write(f"stderr:\n{proc.stderr[:500]}\n")
                return success
            except Exception as e:
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{label}] exception: {e}\n")
                return False

        # Prepare optional Puppeteer no-sandbox configuration (helps on some hardened CI images)
        no_sandbox = (
            os.getenv('MERMAID_NO_SANDBOX', '').lower() in ('1', 'true', 'yes') or
            os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
        )
        pptr_config = None
        pptr_args = []
        if no_sandbox:
            try:
                pptr_config = project_path / 'puppeteer.config.cjs'
                if not pptr_config.exists():
                    pptr_config.write_text(
                        "module.exports = { args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage'] };\n",
                        encoding='utf-8'
                    )
                # mmdc / mermaid-cli use -p or --puppeteerConfigFile
                pptr_args = ['-p', str(pptr_config)]
            except Exception as e:
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"[puppeteer_config] failed to write: {e}\n")

        env_override = os.getenv('MERMAID_CLI_COMMAND')
        if env_override:
            # Split simple commands; if complex, user can provide full quoted string (basic split here)
            cmd = env_override.split() + ['-i', str(mermaid_file), '-o', str(svg_out), '--quiet'] + pptr_args
            run_cmd(cmd, 'env_override_svg')
            cmd = env_override.split() + ['-i', str(mermaid_file), '-o', str(png_out), '--quiet'] + pptr_args
            run_cmd(cmd, 'env_override_png')
            if svg_out.exists() and png_out.exists():
                return

        # Strategy 2: direct mmdc if present
        if shutil.which('mmdc'):
            run_cmd(['mmdc', '-i', str(mermaid_file), '-o', str(svg_out), '--quiet', *pptr_args], 'mmdc_svg')
            run_cmd(['mmdc', '-i', str(mermaid_file), '-o', str(png_out), '--quiet', *pptr_args], 'mmdc_png')
            if svg_out.exists() and png_out.exists():
                return

        # Strategy 3: npx invocation (will download if necessary)
        if shutil.which('npx'):
            run_cmd(['npx', '-y', '@mermaid-js/mermaid-cli', '-i', str(mermaid_file), '-o', str(svg_out), '--quiet', *pptr_args], 'npx_svg')
            run_cmd(['npx', '-y', '@mermaid-js/mermaid-cli', '-i', str(mermaid_file), '-o', str(png_out), '--quiet', *pptr_args], 'npx_png')

        # Strategy 4: direct 'mermaid' binary (newer CLI exposes this) if present
        if not svg_out.exists() and shutil.which('mermaid'):
            run_cmd(['mermaid', '-i', str(mermaid_file), '-o', str(svg_out), *pptr_args], 'mermaid_bin_svg')
            run_cmd(['mermaid', '-i', str(mermaid_file), '-o', str(png_out), *pptr_args], 'mermaid_bin_png')

        # Strategy 5: direct node module execution if node present but above failed
        if not svg_out.exists():
            node_path = shutil.which('node')
            if node_path:
                candidates = []
                # Common global install locations to probe
                possible_roots = [
                    Path(node_path).parent / 'node_modules',
                    Path('/usr/lib/node_modules'),
                    Path('/usr/local/lib/node_modules'),
                    Path(os.getenv('NVM_HOME', '')) / 'node_modules',
                    Path(os.getenv('APPDATA', '')) / 'npm' / 'node_modules'
                ]
                for root in possible_roots:
                    if root and root.exists():
                        for rel in [
                            '@mermaid-js/mermaid-cli/src/cli.js',
                            '@mermaid-js/mermaid-cli/dist/index.cjs',
                            '@mermaid-js/mermaid-cli/dist/index.js',
                            '@mermaid-js/mermaid-cli/dist/cli/index.js'
                        ]:
                            candidate = root / rel
                            if candidate.exists():
                                candidates.append(candidate)
                for c in candidates[:1]:  # first match
                    run_cmd([node_path, str(c), '-i', str(mermaid_file), '-o', str(svg_out), '--quiet'], 'node_direct_svg')
                    run_cmd([node_path, str(c), '-i', str(mermaid_file), '-o', str(png_out), '--quiet'], 'node_direct_png')
                    if svg_out.exists():
                        break

        # If still missing, append summary
        if not svg_out.exists():
            with open(log_file, 'a', encoding='utf-8') as lf:
                lf.write("SVG generation failed after attempts: " + ', '.join(attempts) + "\n")
        if not png_out.exists():
            with open(log_file, 'a', encoding='utf-8') as lf:
                lf.write("PNG generation failed after attempts: " + ', '.join(attempts) + "\n")