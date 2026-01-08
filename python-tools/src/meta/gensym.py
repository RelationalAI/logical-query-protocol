"""Symbol generation utilities."""

from itertools import count
from typing import Iterator

_global_id: Iterator[int] = count(0)

def next_id() -> int:
    return next(_global_id)

def gensym(prefix: str = "_t") -> str:
    return f"{prefix}{next_id()}"

def reset(n=0) -> None:
    """Reset the global ID counter to n (default 0)."""
    global _global_id
    _global_id = count(n)
