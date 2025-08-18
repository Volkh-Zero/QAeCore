from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import json

"""
State persistence & mythic pathing
---------------------------------
Historically the Archon's state lived at (legacy, auto-migrated if present):
    hermetic_engine__persistent_data/state/archon_state.json

In the project mythology the state machine properly belongs under the
Mnemosyne Engine (State Machine). We now store the canonical state at:
    hermetic_engine__persistent_data/Mnemosyne_Engine(State_Machine)/state/archon_state.json

We retain *transparent migration* from the legacy location. On first load:
    - If the new canonical file does not exist but the legacy one does, we move it.
    - Saves always write to the canonical path and (optionally) also mirror to the
        legacy path for backward compatibility until all tooling / docs are updated.
"""

BASE_PERSIST_DIR = Path(__file__).resolve().parent.parent / "hermetic_engine__persistent_data"

# New canonical (mythic) location
MNEMOSYNE_STATE_DIR = BASE_PERSIST_DIR / "Mnemosyne_Engine(State_Machine)" / "state"
MNEMOSYNE_STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR = MNEMOSYNE_STATE_DIR  # alias used elsewhere
STATE_FILE = STATE_DIR / "archon_state.json"

# Legacy path retained for migration / mirroring
LEGACY_STATE_DIR = BASE_PERSIST_DIR / "state"
LEGACY_STATE_FILE = LEGACY_STATE_DIR / "archon_state.json"
LEGACY_STATE_DIR.mkdir(parents=True, exist_ok=True)


class InsightCandidate(BaseModel):
    id: str
    summary: str
    tags: List[str] = []
    confidence: float = 0.5
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ArchonState(BaseModel):
    thread_id: str = "default"
    phase: str = "exploration"
    focus_topic: Optional[str] = None
    open_questions: List[str] = []
    working_hypotheses: List[str] = []
    contradictions: List[str] = []
    bias_flags: List[str] = []
    insight_candidates: List[InsightCandidate] = []
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def save(self, path: Path = STATE_FILE, *, mirror_legacy: bool = True) -> None:
        """Persist the Archon state.

        Args:
            path: Primary (canonical) path to write. Defaults to new mythic path.
            mirror_legacy: If True, also write a copy to the legacy location for
                backward compatibility with any external scripts still pointing there.
        """
        self.last_updated = datetime.now(timezone.utc).isoformat()
        data = self.model_dump()
        serialized = json.dumps(data, indent=2)
        path.write_text(serialized, encoding="utf-8")
        if mirror_legacy and path != LEGACY_STATE_FILE:
            try:
                LEGACY_STATE_FILE.write_text(serialized, encoding="utf-8")
            except Exception:
                # Non-fatal; we silently ignore mirroring failures.
                pass

    @classmethod
    def load(cls, path: Path = STATE_FILE) -> "ArchonState":
        """Load (and if needed migrate) the Archon state.

        Migration logic:
            - If canonical file missing but legacy exists, move legacy → canonical.
            - If neither exists, create a fresh default state at canonical path.
        """
        if not path.exists():
            if LEGACY_STATE_FILE.exists():
                try:
                    # Move legacy file into new canonical location.
                    path.parent.mkdir(parents=True, exist_ok=True)
                    LEGACY_STATE_FILE.replace(path)
                except Exception:
                    # Fallback: copy contents if atomic move fails (e.g. cross-device).
                    try:
                        path.write_text(LEGACY_STATE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
                    except Exception:
                        pass
            if not path.exists():
                # Still absent: create fresh default.
                state = cls()
                state.save(path)
                return state
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)

    # Convenience transitions
    def register_insight(self, summary: str, tags: Optional[List[str]] = None, confidence: float = 0.5):
        ic = InsightCandidate(id=f"ic-{len(self.insight_candidates)+1}", summary=summary, tags=tags or [], confidence=confidence)
        self.insight_candidates.append(ic)

    def flag_contradiction(self, text: str):
        self.contradictions.append(text)

    def flag_bias(self, text: str):
        self.bias_flags.append(text)
