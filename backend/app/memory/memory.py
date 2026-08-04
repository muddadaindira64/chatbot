import json
from pathlib import Path

from app.memory.models import MemoryStore


MEMORY_FILE = Path("memory.json")


def load_memory() -> MemoryStore:

    if not MEMORY_FILE.exists():
        return MemoryStore()

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return MemoryStore(**data)



def save_memory(memory: MemoryStore):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memory.model_dump(),
            f,
            indent=4,
            ensure_ascii=False
        )