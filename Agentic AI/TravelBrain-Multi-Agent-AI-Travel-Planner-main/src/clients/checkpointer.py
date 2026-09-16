"""In-memory checkpointer — no PostgreSQL required for local development."""

from langgraph.checkpoint.memory import MemorySaver

# A single shared MemorySaver instance for the whole process.
# Conversations live in RAM only, they are lost on restart.
_memory_saver = MemorySaver()


def get_checkpointer(_database_url: str = "") -> MemorySaver:
    """Return the in-memory checkpointer. The database_url arg is ignored."""
    return _memory_saver


def get_session_checkpointer() -> MemorySaver:
    """Alias used by other modules."""
    return _memory_saver
