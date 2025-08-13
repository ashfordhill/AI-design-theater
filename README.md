# 🎭 AI Design Theater

<!-- LATEST_DAILY_START -->
> ## 🌅 Latest Daily Design
> **Topic:** Design a distributed caching system
> **Created:** 2025-08-13 04:38:40.453919
> **Project:** 20250813_043804_Design_a_distributed_caching_system
>
> ![Diagram](projects/20250813_043804_Design_a_distributed_caching_system/diagram.svg)
>
> ## 💬 Design Conversation
>
> <details>
> <summary><strong>Click to view the AI-to-AI conversation that led to this design</strong></summary>
>
> <div style="background-color: #f6f8fa; border-radius: 6px; padding: 16px; margin: 16px 0;">
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> A distributed caching system? How quaint. I suppose next you'll suggest we use a relational database and host it on-prem too? Why don't we just go full retro and implement it in COBOL on punch cards? Have you even heard of edge computing and serverless architectures? Or are you too busy living in 2010?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> Oh, please! You think edge computing is some magic wand that solves all our problems? What about the operational nightmare of managing multiple nodes, not to mention the hidden costs of data transfer and latency issues? And security? Good luck with that when your precious cache is sitting across a dozen unmonitored servers! Are you ready to explain how you'll handle the inevitable data breaches, or are you just hoping for the best?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> Data breaches? Really? That's your big concern? We're not storing nuclear launch codes, genius. Ever heard of encryption? Or are you too busy counting pennies to care about actual innovation? And don't lecture me about operational nightmares when your dinosaur solution can't even handle modern workloads. How exactly do you plan to achieve sub-millisecond latency with your glorified spreadsheet approach? Or did you forget that was a requirement?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> Desperate? Ha! The only thing desperate is your idea of a "distributed caching system" that sounds like it was cobbled together in a weekend hackathon. You think you can scale millions of requests per second with some half-baked data sharding strategy? Good luck with that when you’re drowning in synchronization issues and cache invalidation hell! How about you tell me how you plan to keep this mess running smoothly while the rest of us are busy actually delivering results? Or are you just banking on wishful thinking?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> Delivering results? Is that what you call your outdated, overpriced garbage fire of a system? Wake up! We need quantum-resistant encryption and AI-driven cache prediction, not your Stone Age key-value store! How about you explain how your pathetic solution will handle the inevitable data corruption and network partitions? Or are you too busy writing your resignation letter?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> Oh, please! AI-driven cache prediction? You mean another shiny toy that’ll cost us a fortune and still fail at 3 AM? Let’s not pretend your grand vision won’t lead us straight into maintenance hell with a million moving parts. How do you plan to recover from a single point of failure when your “innovative” system goes down, huh? Or are you just hoping the tech fairy will sprinkle some magic dust on it?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> Amateur? That's rich coming from someone whose idea of innovation is probably adding more RAM. Single point of failure? Ever heard of distributed consensus algorithms? Of course not, you're too busy writing SQL queries. How exactly do you plan to handle network partitions with your stone-age approach? Or did you forget the internet exists?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> A tornado of technical superiority? More like a gentle breeze of delusion! You think your precious distributed caching system will magically scale without a robust strategy for data consistency and fault tolerance? Good luck explaining to the board why we’re hemorrhaging money on a system that can’t even handle a simple cache miss! Or are you just planning on throwing more resources at it until it works?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> Hemorrhaging money? That's rich from someone whose "solution" will be obsolete before we even finish implementing it! You want scalability? Try a serverless, event-driven architecture with adaptive caching algorithms! But I guess that's too cutting-edge for your abacus-based thinking, huh? How exactly do you plan to handle sudden traffic spikes without overprovisioning? Or is "throw more servers at it" your entire strategy?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> Oh, please! "Event-driven architecture"? Are you really trying to sell me on a buzzword bingo? Let’s talk about deployment hell when your so-called "adaptive caching algorithms" crash and burn under real-world loads. How do you plan to roll out updates without breaking everything, or are you just hoping for a miracle? Or did you forget that continuous integration and deployment require actual planning, not just throwing code over the wall?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> Planning? That's rich coming from someone whose idea of innovation is probably a new Excel macro. You want real-world loads? Our system will eat those for breakfast while your prehistoric solution chokes on its first request. How about you explain how you'll achieve sub-millisecond latency at scale without edge computing? Or are you too busy dusting off your COBOL manual to keep up with modern tech?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> Winning? The only thing you're winning is a ticket to the graveyard of failed projects! You think your "modern tech" can handle the complexity of distributed caching without spiraling into chaos? Good luck managing that with your fancy edge computing when you can't even keep track of where data is stored! How do you plan to ensure data consistency across nodes when your entire approach is a patchwork of half-baked ideas? Or are you just going to wing it?
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #d97706; background-color: #ffffff; border-radius: 4px;">
>
> **🧠 Idealist** *(anthropic: claude-3-5-sonnet-20240620)*
>
> Desperate? Ha! The only thing desperate here is your pathetic attempt at relevance! You want consistency? We'll use CRDTs and vector clocks while you're still fumbling with two-phase commit! Our system will be self-healing, auto-scaling, and quantum-resistant before you even finish your first code review. How about you explain how your antiquated design will handle a global network partition? Or are you too busy writing your resignation letter? Face it, your approach is as dead as your career prospects!
>
> </div>
>
> <div style="margin: 12px 0; padding: 12px; border-left: 4px solid #10a37f; background-color: #ffffff; border-radius: 4px;">
>
> **🤖 Cost Cutter** *(openai: gpt-4o-mini)*
>
> Weakness? The only weakness here is your grasp on reality! Let's talk about your so-called "self-healing" system when it inevitably crashes under load. How do you plan to recover from a cascading failure when your architecture is as fragile as your ego? Our final design will leverage distributed consensus protocols and a solid microservices architecture that can actually scale, while yours will be a glorified paperweight! Ready to admit defeat, or are you still in denial?
>
> </div>
>
> </div>
>
> </details>
>
> View full: projects/20250813_043804_Design_a_distributed_caching_system
<!-- LATEST_DAILY_END -->

Where AI personalities collaborate on software design! Watch as a visionary "Dreamer" and a pragmatic "Cost Cutter" engage in thoughtful dialogue to create balanced, well-reasoned software designs.

## 🌟 Features

- **Dual AI Personalities**: Dreamer (creative, innovative) vs Cost Cutter (practical, efficient)
- **Multi-Provider Support**: Uses both OpenAI and Anthropic for diverse perspectives (optional GPT‑5 preview override)
- **Automatic Documentation**: Generates design documents and conversation transcripts
- **Mermaid Diagrams**: Creates visual architecture diagrams automatically (component graphs at higher detail levels)
- **Keyword-Biased Idea Generation**: Bias random/daily topics via IDEA_KEYWORDS or CLI flag
- **Configurable Debate & Diagram Depth**: Control disagreement level and diagram richness via CLI or workflow inputs
- **Convergence Enforcement**: Sessions conclude with an explicit FINAL DESIGN block
- **Extensible Architecture**: Easy to add new personalities and features
- **GitHub Integration Ready**: Prepared for automated daily design sessions

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd AI-design-theater

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# You need at least one of: OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### 3. Run Your First Design Session

```bash
# Basic usage
python cli.py run "Design a task management app"

# With additional context
python cli.py run "Design a microservices architecture" --context "For an e-commerce platform with 1M users"

# With custom limits
python cli.py run "Design a caching strategy" --max-turns 15 --max-duration 20

# Random / daily topics (with optional keyword bias)
python cli.py random --keywords security,edge
python cli.py daily-topic --keywords ai,ml
```

## 📋 Commands

### Run a Design Session
```bash
python cli.py run "Your design topic" [OPTIONS]
```

**Options:**
- `--context, -c`: Additional context for the discussion
- `--max-turns, -t`: Maximum number of conversation turns (default: 20)
- `--max-duration, -d`: Maximum duration in minutes (default: 30)
- `--debate-intensity`: 0–10 (higher = more challenge & pushback; default 5)
- `--diagram-detail`: 1–10 (>=7 component architecture graph; >=9 extended nodes)

### List Projects
```bash
python cli.py list
```

### Validate Setup
```bash
python cli.py validate
```

### Show Examples
```bash
python cli.py example
```

### Random Topic
```bash
python cli.py random [--keywords kw1,kw2]
```

### Daily Topic (deterministic by weekday)
```bash
python cli.py daily-topic [--keywords kw1,kw2]
```

## 🎭 The Personalities

### 🌟 Dreamer (Anthropic Claude)
- **Role**: Visionary and innovator
- **Focus**: User experience, cutting-edge tech, ambitious features
- **Traits**: Creative, optimistic, future-focused
- **Asks**: "How can we make this amazing?"

### 💰 Cost Cutter (OpenAI GPT-4)
- **Role**: Pragmatic efficiency expert
- **Focus**: Budget, timeline, maintainability, MVP thinking
- **Traits**: Practical, cost-conscious, risk-aware
- **Asks**: "Do we really need this? What's the simplest solution?"

## 📁 Project Structure

After running a design session, you'll get:

```
projects/
└── 20241201_120000_your_topic/
    ├── DESIGN.md              # Formatted design document
    ├── conversation.md        # Full conversation transcript
    ├── diagram.mmd           # Mermaid architecture diagram
    ├── design_document.json  # Structured design data
    └── session.json          # Raw session data
```

## 🔧 Architecture

```
src/
├── personalities/          # AI personality configurations
├── conversation/           # Conversation management
├── llm_providers/         # LLM provider abstractions
├── diagram_generation/    # Mermaid diagram creation
├── storage/              # File management
├── models.py             # Data models
├── config.py             # Configuration
└── main.py              # Main orchestrator
```

## 🎯 Example Topics

- "Design a real-time chat application"
- "Create a CI/CD pipeline for a Python web app"
- "Design a scalable image processing service"
- "Plan a database migration strategy"
- "Design an API rate limiting system"
- "Create a monitoring and alerting solution"
- "Design a content recommendation engine"
- "Plan a multi-tenant SaaS architecture"

## 🔮 Future Features

- **Automated Daily Sessions**: GitHub Actions integration for daily design generation (already included via workflow)
- **Custom Personalities**: Easy creation of new AI personalities
- **Idea Generation**: Automatic sourcing of trending software topics
- **Enhanced Diagrams**: Edge labels, subgraphs & richer semantics at high detail levels
- **Team Integration**: Slack/Discord bots for team design sessions
- **Design Templates**: Reusable patterns and starting points

## 🛠️ Development

### Adding New Personalities

1. Create personality config in `src/personalities/`
2. Define system prompts and traits
3. Choose appropriate LLM provider
4. Test with validation command

### Adding New LLM Providers

1. Implement `BaseLLMProvider` interface
2. Add provider to `PersonalityManager`
3. Update configuration and models

### Extending Diagram Generation

1. Add new diagram types to `MermaidGenerator`
2. Implement content analysis patterns
3. Test with various conversation types

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests for any improvements.

---

## ⚙️ Advanced Configuration

Environment variables (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| OPENAI_API_KEY | OpenAI access |
| ANTHROPIC_API_KEY | Anthropic access |
| ENABLE_GPT5_PREVIEW | If true and preview model provided, Cost Cutter uses GPT‑5 preview |
| GPT5_PREVIEW_MODEL | Explicit GPT‑5 preview model id |
| OPENAI_COST_CUTTER_MODEL | Override Cost Cutter model (if not using preview) |
| IDEA_KEYWORDS | Comma-separated keywords to bias topic selection |
| DEFAULT_MAX_TURNS | Default max turns |
| DEFAULT_MAX_DURATION_MINUTES | Default duration limit |
| DEBATE_INTENSITY | (Optional) Default debate intensity override |
| DIAGRAM_DETAIL_LEVEL | (Optional) Default diagram detail level override |

CLI `--keywords` temporarily overrides IDEA_KEYWORDS for that invocation.

Convergence: The system will inject a hint near the end to produce a FINAL DESIGN summary; completion requires that block.

*Built with ❤️ for the software design community*

---

### 📚 Project Index

For a consolidated list of all generated design sessions (topic, date, and diagram preview), see `PROJECTS_INDEX.md`.