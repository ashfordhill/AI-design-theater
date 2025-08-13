"""Stance memory persistence for personalities.

Lightweight mechanism to remember per-personality principles and simple
interaction counters across sessions. Enables personalities to periodically
reaffirm or lean on consistent viewpoints, creating a sense of continuity.

The memory file is a JSON blob per personality name stored under
``data/stance_memory/<PersonalityName>.json`` relative to project root.
If the file does not exist, a seed set of principles is created.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

DEFAULT_PRINCIPLES: Dict[str, List[str]] = {
    "Idealist": [
        "Push revolutionary tech that transforms entire industries - mediocrity is death",
        "Embrace bleeding-edge solutions that separate winners from losers", 
        "Innovation requires risk - safe choices are career suicide",
    ],
    "Cost Cutter": [
        "Every dollar wasted is a dollar that could save someone's job",
        "Proven tech survives 3am disasters - fancy toys create them",
        "Complexity is the enemy - simple solutions scale, complex ones collapse",
    ],
}


class StanceMemoryManager:
    """Loads, updates, and persists stance memory for personalities."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = (base_dir or Path("data") / "stance_memory").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _file_for(self, name: str) -> Path:
        safe = "".join(c for c in name if c.isalnum() or c in ("_", "-")) or "persona"
        return self.base_dir / f"{safe}.json"

    def load(self, name: str) -> Dict[str, Any]:
        path = self._file_for(name)
        if not path.exists():
            data = {
                "name": name,
                "principles": DEFAULT_PRINCIPLES.get(name, [
                    "Maintain architectural coherence",
                    "Balance innovation with practicality",
                ]),
                "challenge_count": 0,
                "agreement_count": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }
            self.save(name, data)
            return data
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.load(name)  # recreate

    def save(self, name: str, memory: Dict[str, Any]):
        memory["last_updated"] = datetime.utcnow().isoformat()
        path = self._file_for(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)

    def analyze_and_update_counts(self, name: str, messages: List[str]):
        """Increment simple interaction counters based on message content list."""
        memory = self.load(name)
        for m in messages:
            lower = m.lower()
            if any(w in lower for w in ["i disagree", "push back", "challenge", "concern", "risk"]):
                memory["challenge_count"] += 1
            if any(w in lower for w in ["agree", "sounds good", "makes sense", "concur"]):
                memory["agreement_count"] += 1
        self.save(name, memory)

    def pick_principle(self, name: str, turn_index: int) -> str | None:
        memory = self.load(name)
        principles = memory.get("principles", [])
        if not principles:
            return None
        # Rotate principles deterministically by turn index for reproducibility.
        return principles[turn_index % len(principles)]
