"""Simple web viewer for AI Design Theater conversations (optional)."""

import json
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# This is a simple example - in production you might use FastAPI, Flask, or Streamlit
# For now, this generates static HTML files that can be viewed in a browser


class ConversationWebViewer:
    """Generate HTML views of conversations."""
    
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = Path(projects_dir)
    
    def generate_project_html(self, project_path: Path) -> str:
        """Generate HTML for a single project."""
        session_file = project_path / "session.json"
        design_file = project_path / "design_document.json"
        
        if not session_file.exists():
            return "<p>Session data not found</p>"
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        design_data = {}
        if design_file.exists():
            with open(design_file, 'r', encoding='utf-8') as f:
                design_data = json.load(f)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Design Theater - {session_data.get('config', {}).get('topic', 'Unknown')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .conversation {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                .dreamer {{ border-left: 4px solid #4CAF50; }}
                .cost-cutter {{ border-left: 4px solid #FF9800; }}
                .system {{ border-left: 4px solid #2196F3; }}
                .speaker {{ font-weight: bold; color: #333; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
                .design-doc {{ background: #fff; padding: 20px; border-radius: 8px; margin-top: 20px; }}
                .mermaid {{ background: #f5f5f5; padding: 15px; border-radius: 4px; font-family: monospace; }}
                pre {{ white-space: pre-wrap; }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        </head>
        <body>
            <div class="header">
                <h1>🎭 AI Design Theater</h1>
                <h2>{session_data.get('config', {}).get('topic', 'Unknown Topic')}</h2>
                <p><strong>Participants:</strong> {', '.join([p.get('name', 'Unknown') for p in session_data.get('participants', [])])}</p>
                <p><strong>Started:</strong> {session_data.get('started_at', 'Unknown')}</p>
                <p><strong>Status:</strong> {session_data.get('status', 'Unknown')}</p>
                {f"<p><strong>Context:</strong> {session_data.get('config', {}).get('context', '')}</p>" if session_data.get('config', {}).get('context') else ''}
            </div>
        """
        
        # Add conversation messages
        messages = session_data.get('messages', [])
        for message in messages:
            speaker = message.get('speaker', 'System')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            css_class = 'system'
            if speaker == 'Dreamer':
                css_class = 'dreamer'
            elif speaker == 'Cost Cutter':
                css_class = 'cost-cutter'
            
            html += f"""
            <div class="conversation {css_class}">
                <div class="speaker">{speaker}</div>
                <div class="timestamp">{timestamp}</div>
                <div class="content">{content.replace(chr(10), '<br>')}</div>
            </div>
            """
        
        # Add design document if available
        if design_data:
            html += f"""
            <div class="design-doc">
                <h2>📋 Design Document</h2>
                <h3>{design_data.get('title', 'Untitled')}</h3>
                <p>{design_data.get('description', '')}</p>
                
                {f"<h4>Key Decisions</h4><ul>{''.join([f'<li>{decision}</li>' for decision in design_data.get('key_decisions', [])])}</ul>" if design_data.get('key_decisions') else ''}
                
                {f"<h4>Trade-offs</h4><ul>{''.join([f'<li>{tradeoff}</li>' for tradeoff in design_data.get('trade_offs', [])])}</ul>" if design_data.get('trade_offs') else ''}
                
                {f"<h4>Implementation Notes</h4><ul>{''.join([f'<li>{note}</li>' for note in design_data.get('implementation_notes', [])])}</ul>" if design_data.get('implementation_notes') else ''}
                
                {f'<h4>Architecture Diagram</h4><div class="mermaid">{design_data.get("mermaid_diagram", "")}</div>' if design_data.get('mermaid_diagram') else ''}
            </div>
            """
        
        html += """
            <script>
                mermaid.initialize({startOnLoad:true});
            </script>
        </body>
        </html>
        """
        
        return html
    
    def generate_index_html(self) -> str:
        """Generate index page with all projects."""
        projects = []
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                session_file = project_dir / "session.json"
                if session_file.exists():
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        projects.append({
                            'name': project_dir.name,
                            'topic': session_data.get('config', {}).get('topic', 'Unknown'),
                            'started_at': session_data.get('started_at', 'Unknown'),
                            'status': session_data.get('status', 'Unknown'),
                            'participants': [p.get('name', 'Unknown') for p in session_data.get('participants', [])]
                        })
                    except Exception:
                        continue
        
        # Sort by date (newest first)
        projects.sort(key=lambda x: x['started_at'], reverse=True)
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Design Theater - Projects</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
                .header { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
                .project { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 8px; }
                .project h3 { margin-top: 0; }
                .project a { text-decoration: none; color: #2196F3; }
                .project a:hover { text-decoration: underline; }
                .meta { color: #666; font-size: 0.9em; }
                .status { padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
                .completed { background: #4CAF50; color: white; }
                .timeout { background: #FF9800; color: white; }
                .error { background: #f44336; color: white; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎭 AI Design Theater</h1>
                <p>Collaborative AI Design Sessions</p>
            </div>
        """
        
        if not projects:
            html += "<p>No design projects found. Run a design session to get started!</p>"
        else:
            for project in projects:
                status_class = project['status'].replace('_', '-')
                html += f"""
                <div class="project">
                    <h3><a href="{project['name']}.html">{project['topic']}</a></h3>
                    <div class="meta">
                        <span class="status {status_class}">{project['status']}</span>
                        Participants: {', '.join(project['participants'])} | 
                        Started: {project['started_at'][:19] if len(project['started_at']) > 19 else project['started_at']}
                    </div>
                </div>
                """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def generate_all_html_files(self, output_dir: str = "web_output"):
        """Generate HTML files for all projects."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate index
        index_html = self.generate_index_html()
        with open(output_path / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        # Generate individual project pages
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                session_file = project_dir / "session.json"
                if session_file.exists():
                    project_html = self.generate_project_html(project_dir)
                    html_filename = f"{project_dir.name}.html"
                    with open(output_path / html_filename, 'w', encoding='utf-8') as f:
                        f.write(project_html)
        
        print(f"HTML files generated in {output_path}")
        print(f"Open {output_path}/index.html in your browser to view projects")


if __name__ == "__main__":
    viewer = ConversationWebViewer()
    viewer.generate_all_html_files()