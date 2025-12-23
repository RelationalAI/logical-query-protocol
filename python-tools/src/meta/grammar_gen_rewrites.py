"""Grammar rule rewrites for transforming protobuf-generated rules.

These rewrites transform grammar rules generated from protobuf definitions
into forms more suitable for parsing S-expressions.
"""

from typing import Callable, List, Optional

from .grammar import Rule


def get_rule_rewrites() -> List[Callable[[Rule], Optional[Rule]]]:
    """Return rule rewrite functions.

    These rewrites transform grammar rules generated from protobuf definitions
    into forms more suitable for parsing S-expressions.

    Each rewrite function takes a Rule and returns either a rewritten Rule
    or None if the rewrite doesn't apply.

    Returns:
        A list of rewrite functions to apply to generated rules.
    """
    return []
