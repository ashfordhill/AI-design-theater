"""Example script demonstrating AI Design Theater usage."""

import asyncio
import os
from src.main import AIDesignTheater


async def main():
    """Run an example design session."""
    
    # Check if API keys are configured
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("❌ No API keys found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables")
        print("Or create a .env file with your keys")
        return
    
    print("🎭 AI Design Theater - Example Session")
    print("=" * 50)
    
    # Initialize the theater
    theater = AIDesignTheater()
    
    # Validate setup
    print("🔍 Validating setup...")
    validation = await theater.validate_setup()
    
    if not validation["api_keys"]:
        print("❌ API keys not properly configured")
        return
    
    print("✅ Setup validated!")
    print(f"   OpenAI: {'✅' if validation['openai_connection'] else '❌'}")
    print(f"   Anthropic: {'✅' if validation['anthropic_connection'] else '❌'}")
    print()
    
    # Example design topics
    topics = [
        {
            "topic": "Design a real-time collaborative document editor",
            "context": "Think Google Docs but for code editing, supporting multiple programming languages"
        },
        {
            "topic": "Create a scalable image processing pipeline",
            "context": "Handle millions of images per day with various transformations and optimizations"
        },
        {
            "topic": "Design a microservices monitoring system",
            "context": "Track health, performance, and dependencies across 50+ services"
        }
    ]
    
    print("🎯 Available example topics:")
    for i, example in enumerate(topics, 1):
        print(f"   {i}. {example['topic']}")
    print()
    
    # Let user choose or use first one
    try:
        choice = input("Choose a topic (1-3) or press Enter for topic 1: ").strip()
        if choice and choice.isdigit() and 1 <= int(choice) <= 3:
            selected = topics[int(choice) - 1]
        else:
            selected = topics[0]
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    print(f"🚀 Starting design session: {selected['topic']}")
    print(f"📝 Context: {selected['context']}")
    print()
    
    try:
        # Run the design session
        project_dir = await theater.run_design_session(
            topic=selected['topic'],
            context=selected['context'],
            max_turns=12,  # Shorter for demo
            max_duration_minutes=15  # Shorter for demo
        )
        
        print()
        print("🎉 Design session completed!")
        print(f"📁 Project saved to: {project_dir}")
        print()
        print("📄 Generated files:")
        print(f"   • DESIGN.md - Formatted design document")
        print(f"   • conversation.md - Full conversation transcript")
        print(f"   • diagram.mmd - Mermaid architecture diagram")
        print(f"   • design_document.json - Structured data")
        print()
        print("💡 Tip: You can view the Mermaid diagram at https://mermaid.live/")
        
    except Exception as e:
        print(f"❌ Error during design session: {e}")
        print("Please check your API keys and network connection")


if __name__ == "__main__":
    asyncio.run(main())