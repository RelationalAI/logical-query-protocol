"""Symbol generation utilities.

This module provides functions for generating unique variable names during
grammar and code generation. It maintains a global counter to ensure
uniqueness across all generated symbols.

The primary use case is generating temporary variables in semantic actions
when transforming grammar rules or inlining lambda expressions.

Example:
    >>> from meta.gensym import gensym, reset
    >>> reset(0)  # Start from 0 for predictable output
    >>> gensym()
    '_t0'
    >>> gensym('var')
    'var1'
    >>> gensym('tmp')
    'tmp2'
"""

from itertools import count
from typing import Iterator

_global_id: Iterator[int] = count(0)

def reset(start: int = 0) -> None:
    """Reset the global ID counter.

    Args:
        start: The starting value for the counter (default: 0)

    Note:
        This is primarily useful for testing to ensure deterministic output.
    """
    global _global_id
    _global_id = count(start)

def next_id() -> int:
    """Return the next unique ID from the global counter.

    Returns:
        An integer that has not been returned before.
    """
    return next(_global_id)

def gensym(prefix: str = "_t") -> str:
    """Generate a unique symbol name with the given prefix.

    Args:
        prefix: Prefix for the generated symbol (default: "_t")

    Returns:
        A unique string of the form "{prefix}{id}"

    Example:
        >>> reset(0)
        >>> gensym()
        '_t0'
        >>> gensym('temp')
        'temp1'
    """
    return f"{prefix}{next_id()}"
