import os, re, pathlib

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
    block = [
        '> ## 🌅 Latest Daily Design',
        f"> **Topic:** {latest['topic']}",
        f"> **Created:** {latest['created'] or 'Unknown'}",
        f"> **Project:** {latest['folder']}",
        '>',
        diagram_section,
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
