"""Setup script for AI Design Theater."""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ .env file created! Please edit it with your API keys.")
        return True
    elif env_file.exists():
        print("✅ .env file already exists.")
        return False
    else:
        print("❌ .env.example not found!")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ["projects", "web_output"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed!")


def run_validation():
    """Run validation to check setup."""
    print("🔍 Running setup validation...")
    os.system("python cli.py validate")


def main():
    """Main setup function."""
    print("🎭 AI Design Theater Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .env file
    env_created = create_env_file()
    
    # Install dependencies
    install_dependencies()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    
    if env_created:
        print("1. Edit .env file with your API keys:")
        print("   - OPENAI_API_KEY=your_key_here")
        print("   - ANTHROPIC_API_KEY=your_key_here")
        print("   (You need at least one API key)")
    
    print("2. Validate your setup:")
    print("   python cli.py validate")
    
    print("3. Run your first design session:")
    print("   python cli.py run \"Design a task management app\"")
    
    print("4. View examples:")
    print("   python cli.py example")
    
    print("\n💡 Pro tip: Run 'python example.py' for an interactive demo!")


if __name__ == "__main__":
    main()