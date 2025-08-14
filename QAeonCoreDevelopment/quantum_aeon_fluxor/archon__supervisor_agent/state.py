from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import json

STATE_DIR = Path(__file__).resolve().parent.parent / "hermetic_engine__persistent_data" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "archon_state.json"


class InsightCandidate(BaseModel):
    id: str
    summary: str
    tags: List[str] = []
    confidence: float = 0.5
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ArchonState(BaseModel):
    thread_id: str = "default"
    phase: str = "exploration"
    focus_topic: Optional[str] = None
    open_questions: List[str] = []
    working_hypotheses: List[str] = []
    contradictions: List[str] = []
    bias_flags: List[str] = []
    insight_candidates: List[InsightCandidate] = []
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def save(self, path: Path = STATE_FILE) -> None:
        self.last_updated = datetime.utcnow().isoformat()
        data = json.loads(self.model_json(indent=2))
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = STATE_FILE) -> "ArchonState":
        if not path.exists():
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
