import os, re, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECTS = ROOT / 'projects'
README = ROOT / 'README.md'
INDEX = ROOT / 'PROJECTS_INDEX.md'

LATEST_START = '<!-- LATEST_DAILY_START -->'
LATEST_END = '<!-- LATEST_DAILY_END -->'

def load_projects():
    items = []
    if not PROJECTS.exists():
        return items
    for name in sorted(p for p in os.listdir(PROJECTS) if (PROJECTS / p).is_dir()):
        design = PROJECTS / name / 'DESIGN.md'
        diagram = PROJECTS / name / 'diagram.mmd'
        diagram_png = PROJECTS / name / 'diagram.png'
        diagram_svg = PROJECTS / name / 'diagram.svg'
        convo = PROJECTS / name / 'conversation.md'
        topic_part = name.split('_', 2)[-1].replace('_',' ')
        created = ''
        if design.exists():
            m = re.search(r'\*\*Created:\*\*\s*(.*)', design.read_text(encoding='utf-8'))
            if m:
                created = m.group(1).strip()
        mermaid = ''
        if design.exists():
            mm = re.search(r'```mermaid(.*?)```', design.read_text(encoding='utf-8'), re.S)
            if mm:
                mermaid = '```mermaid' + mm.group(1).strip('\n') + '\n```'
        items.append({
            'folder': name,
            'topic': topic_part,
            'created': created,
            'has_design': design.exists(),
            'has_diagram': diagram.exists(),
            'has_diagram_png': diagram_png.exists(),
            'has_convo': convo.exists(),
            'has_diagram_svg': diagram_svg.exists(),
            'mermaid': mermaid
        })
    return items

def extract_conversation_logs(project_folder):
    """Extract formatted conversation logs from a project."""
    session_file = PROJECTS / project_folder / 'session.json'
    if not session_file.exists():
        return ""
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        messages = session_data.get('messages', [])
        participants = session_data.get('participants', [])
        
        # Create participant lookup for styling
        participant_info = {}
        for p in participants:
            name = p.get('name', '')
            provider = p.get('provider', '')
            model = p.get('model', '')
            participant_info[name] = {
                'provider': provider,
                'model': model,
                'emoji': '🤖' if provider == 'openai' else '🧠' if provider == 'anthropic' else '💭'
            }
        
        conversation_lines = []
        conversation_lines.append('> ## 💬 Design Conversation')
        conversation_lines.append('>')
        conversation_lines.append('> <details>')
        conversation_lines.append('> <summary><strong>Click to view the AI-to-AI conversation that led to this design</strong></summary>')
        conversation_lines.append('>')
        conversation_lines.append('> <div style="background-color: #f6f8fa; border-radius: 6px; padding: 16px; margin: 16px 0;">')
        conversation_lines.append('>')
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            speaker = message.get('speaker', '')
            
            # Skip system prompts and referee messages
            if role == 'user' or 'REFEREE' in content or 'System Prompt' in content:
                continue
            
            if role == 'assistant' and speaker and speaker in participant_info:
                info = participant_info[speaker]
                emoji = info['emoji']
                provider_model = f"{info['provider']}: {info['model']}"
                
                # Create a styled conversation bubble
                border_color = '#10a37f' if info['provider'] == 'openai' else '#d97706' if info['provider'] == 'anthropic' else '#6b7280'
                
                conversation_lines.append(f'> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid {border_color}; background-color: #ffffff; border-radius: 4px;">')
                conversation_lines.append('>')
                conversation_lines.append(f'> **{emoji} {speaker}** *({provider_model})*')
                conversation_lines.append('>')
                
                # Split content into lines and add > prefix
                content_lines = content.split('\n')
                for line in content_lines:
                    conversation_lines.append(f'> {line}')
                
                conversation_lines.append('>')
                conversation_lines.append('> </div>')
                conversation_lines.append('>')
        
        conversation_lines.append('> </div>')
        conversation_lines.append('>')
        conversation_lines.append('> </details>')
        
        return '\n'.join(conversation_lines)
        
    except Exception as e:
        return f"> *Error loading conversation: {e}*"

def update_index(projects):
    lines = [
        '# 📚 AI Design Theater Project Index',
        '',
        'Automatically generated list of all projects.',
        ''
    ]
    for p in sorted(projects, key=lambda x: x['created']):
        lines.append(f"### {p['created'] or 'Unknown Date'} — {p['topic']}")
        links = []
        if p['has_design']:
            links.append(f"Design: [DESIGN.md](projects/{p['folder']}/DESIGN.md)")
        if p['has_diagram']:
            links.append(f"Diagram: [diagram.mmd](projects/{p['folder']}/diagram.mmd)")
        if p.get('has_diagram_svg'):
            links.append(f"SVG: [diagram.svg](projects/{p['folder']}/diagram.svg)")
        if p.get('has_diagram_png'):
            links.append(f"PNG: [diagram.png](projects/{p['folder']}/diagram.png)")
        if p['has_convo']:
            links.append(f"Conversation: [conversation.md](projects/{p['folder']}/conversation.md)")
        lines.append(f"- Folder: `projects/{p['folder']}`")
        if links:
            lines.append(f"- {' | '.join(links)}")
        if p.get('has_diagram_svg'):
            lines.append(f"![Diagram](projects/{p['folder']}/diagram.svg)\n")
        elif p.get('has_diagram_png'):
            lines.append(f"![Diagram](projects/{p['folder']}/diagram.png)\n")
        elif p['mermaid']:
            lines.append(p['mermaid'])
        lines.append('')
    INDEX.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')

def update_readme(projects):
    if not projects:
        return
    latest = sorted(projects, key=lambda x: x['folder'])[-1]
    # Prefer PNG image if exists
    latest_svg_path = f"projects/{latest['folder']}/diagram.svg"
    latest_png_path = f"projects/{latest['folder']}/diagram.png"
    has_svg = (PROJECTS / latest['folder'] / 'diagram.svg').exists()
    has_png = (PROJECTS / latest['folder'] / 'diagram.png').exists()
    if has_svg:
        diagram_section = f"> ![Diagram]({latest_svg_path})"
    elif has_png:
        diagram_section = f"> ![Diagram]({latest_png_path})"
    else:
        diagram_section = '> ' + (latest['mermaid'].replace('\n', '\n> ') if latest['mermaid'] else '_No diagram_')
    # Get conversation logs
    conversation_section = extract_conversation_logs(latest['folder'])
    
    block = [
        '> ## 🌅 Latest Daily Design',
        f"> **Topic:** {latest['topic']}",
        f"> **Created:** {latest['created'] or 'Unknown'}",
        f"> **Project:** {latest['folder']}",
        '>',
        diagram_section,
        '>',
        conversation_section,
        '>',
        f"> View full: projects/{latest['folder']}"
    ]
    content = README.read_text(encoding='utf-8')
    pattern = re.compile(f'{LATEST_START}.*?{LATEST_END}', re.S)
    replacement = f"{LATEST_START}\n" + '\n'.join(block) + f"\n{LATEST_END}"
    if pattern.search(content):
        content = pattern.sub(replacement, content)
    else:
        content = replacement + '\n\n' + content
    README.write_text(content, encoding='utf-8')

def main():
    projects = load_projects()
    update_index(projects)
    update_readme(projects)

if __name__ == '__main__':
    main()
