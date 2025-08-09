"""Configuration management for AI Design Theater."""

import os
from typing import Optional, List
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    # API Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Optional model overrides / preview flags
    enable_gpt5_preview: bool = os.getenv("ENABLE_GPT5_PREVIEW", "0").lower() in {"1", "true", "yes"}
    openai_cost_cutter_model: Optional[str] = os.getenv("OPENAI_COST_CUTTER_MODEL")
    gpt5_preview_model: Optional[str] = os.getenv("GPT5_PREVIEW_MODEL")  # if provided and enable flag set
    
    # Conversation defaults
    default_max_turns: int = int(os.getenv("DEFAULT_MAX_TURNS", "20"))
    default_max_duration_minutes: int = int(os.getenv("DEFAULT_MAX_DURATION_MINUTES", "30"))
    default_debate_intensity: int = int(os.getenv("DEBATE_INTENSITY", "5"))
    default_diagram_detail_level: int = int(os.getenv("DIAGRAM_DETAIL_LEVEL", "6"))
    
    # File paths
    projects_dir: str = os.getenv("PROJECTS_DIR", "projects")

    # Idea generation keyword bias (comma separated)
    # Store initial raw but property will re-read environment for dynamic overrides
    idea_keywords_raw: Optional[str] = os.getenv("IDEA_KEYWORDS")

    @property
    def idea_keywords(self) -> List[str]:
        # Always fetch current env to allow runtime overrides (CLI or workflow step)
        raw = os.getenv("IDEA_KEYWORDS", self.idea_keywords_raw or "")
        if not raw:
            return []
        return [k.strip() for k in raw.split(',') if k.strip()]
    
    # GitHub integration (for future use)
    github_token: Optional[str] = os.getenv("GITHUB_TOKEN")
    github_repo: Optional[str] = os.getenv("GITHUB_REPO")
    
    def validate_api_keys(self) -> bool:
        """Check if at least one API key is available."""
        return bool(self.openai_api_key or self.anthropic_api_key)


# Global config instance
config = Config()