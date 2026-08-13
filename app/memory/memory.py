import json
from pathlib import Path

from app.memory.models import MemoryStore


MEMORY_DIR = Path("memory")


def _memory_file(user_id: int) -> Path:
    """Return the per-user memory file path."""
    return MEMORY_DIR / f"user_{user_id}.json"


def load_memory(user_id: int) -> MemoryStore:
    """Load memory for a specific user from their own file."""
    file_path = _memory_file(user_id)

    if not file_path.exists():
        return MemoryStore()

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return MemoryStore(**data)


def save_memory(user_id: int, memory: MemoryStore):
    """Save memory for a specific user to their own file."""
    file_path = _memory_file(user_id)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            memory.model_dump(),
            f,
            indent=4,
            ensure_ascii=False
        )