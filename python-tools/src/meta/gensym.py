"""Symbol generation utilities."""

from itertools import count
from typing import Iterator

_global_id: Iterator[int] = count(0)

def reset(start: int = 0) -> None:
    """Reset the global ID counter. Useful for testing."""
    global _global_id
    _global_id = count(start)

def next_id() -> int:
    return next(_global_id)

def gensym(prefix: str = "_t") -> str:
    return f"{prefix}{next_id()}"
