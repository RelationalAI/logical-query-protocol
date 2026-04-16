#!/usr/bin/env python3
"""Parse grammar.y and generate a clean S-expression grammar in Markdown.

Strips construct/deconstruct actions, type annotations, and protobuf details,
leaving only the pure S-expression syntax.

Usage:
    python grammar_to_markdown.py [grammar.y] [output.md]
"""

import re
import sys
from pathlib import Path


def parse_file(path: str) -> tuple[list, dict, list]:
    """Parse grammar.y into tokens, aliases, and rules."""
    text = Path(path).read_text()
    # Split on %% that appears alone on a line (not inside comments)
    sections = re.split(r"^\s*%%\s*$", text, flags=re.MULTILINE)
    header = sections[0]
    rules_text = sections[1] if len(sections) > 1 else ""

    tokens = []
    aliases = {}

    for line in header.splitlines():
        line = line.strip()
        if line.startswith("%token_alias"):
            parts = line.split()
            aliases[parts[1]] = parts[2]
        elif line.startswith("%token ") and not line.startswith("%token_alias"):
            parts = line.split(None, 3)
            # %token NAME Type PATTERN
            name = parts[1]
            raw_pattern = parts[3] if len(parts) > 3 else ""
            # Strip r'...' or '...' wrapper
            pattern = re.sub(r"^r?'(.*)'$", r"\1", raw_pattern)
            tokens.append((name, pattern))

    rules = parse_rules(rules_text)
    return tokens, aliases, rules


def parse_rules(text: str) -> list[tuple[str, str | None, list[str]]]:
    """Extract rule names, doc-comments, and production alternatives.

    A doc-comment is a block of consecutive #-comment lines immediately
    preceding a rule name (no blank line in between).
    """
    rules = []
    current_rule = None
    current_doc = None
    current_alts = []
    comment_buf: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        # Blank line: reset comment buffer
        if not stripped:
            comment_buf = []
            continue

        # Comment line: accumulate in buffer
        if stripped.startswith("#"):
            comment_buf.append(stripped.lstrip("# "))
            continue

        # Rule name: non-indented identifier
        if line and not line[0].isspace():
            if current_rule and current_alts:
                rules.append((current_rule, current_doc, current_alts))
            current_rule = stripped
            current_doc = "\n".join(comment_buf) if comment_buf else None
            current_alts = []
            comment_buf = []
            continue

        # Production line: starts with : or |
        if stripped.startswith(":") or stripped.startswith("|"):
            prod = stripped[1:].strip()
            current_alts.append(prod)
            comment_buf = []
            continue

        # Everything else is an action line — skip
        comment_buf = []

    if current_rule and current_alts:
        rules.append((current_rule, current_doc, current_alts))

    return rules


def format_production(prod: str, nonterms: set[str]) -> str:
    """Format a single production for markdown display.

    Quoted literals like "(" become `(`, non-terminals become links
    to their definitions, and modifiers (?, *, +) are preserved.
    """
    # Tokenize: quoted strings, symbols with modifiers
    result = []
    for tok in re.findall(r'"(?:[^"\\]|\\.)*"[?*+]?|[^\s]+', prod):
        if tok.startswith('"'):
            # Strip quotes, keep modifier
            m = re.match(r'"(.*)"([?*+]?)', tok)
            if m:
                literal, mod = m.group(1), m.group(2)
                result.append(f'`{literal}`{mod}')
        else:
            # Split off trailing modifier (?, *, +)
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)([?*+]?)$", tok)
            if m and m.group(1) in nonterms:
                name, mod = m.group(1), m.group(2)
                result.append(f"[{name}](#{name}){mod}")
            else:
                result.append(tok)
    return " ".join(result)


def generate_markdown(
    tokens: list, aliases: dict, rules: list[tuple[str, str | None, list[str]]]
) -> str:
    """Generate a markdown document from parsed grammar components."""
    lines = []
    lines.append("# LQP S-Expression Grammar")
    lines.append("")
    lines.append(
        "This document describes the S-expression syntax of the Logical Query Protocol."
    )
    lines.append(
        "It is auto-generated from `grammar.y` with construct/deconstruct actions removed."
    )
    lines.append("")

    # Tokens
    lines.append("## Terminals")
    lines.append("")
    for name, pattern in tokens:
        if pattern:
            lines.append(f"- **{name}** &mdash; `{pattern}`")
        else:
            lines.append(f"- **{name}**")
    lines.append("")

    if aliases:
        lines.append("### Token Aliases (formatted variants)")
        lines.append("")
        lines.append(
            "These are display variants used in the pretty printer;"
            " they parse identically to the base token."
        )
        lines.append("")
        for alias, base in sorted(aliases.items()):
            lines.append(f"- **{alias}** &rarr; {base}")
        lines.append("")

    # Rules
    lines.append("## Grammar Rules")
    lines.append("")

    nonterms = {name for name, _, _ in rules}

    for rule_name, doc, alts in rules:
        lines.append(f"### {rule_name}")
        lines.append("")
        if doc:
            lines.append(doc)
            lines.append("")
        for i, alt in enumerate(alts):
            if i == 0:
                lines.append(f"&ensp;{format_production(alt, nonterms)}  ")
            else:
                lines.append(f"| {format_production(alt, nonterms)}  ")
        lines.append("")

    return "\n".join(lines)


def main():
    grammar_path = sys.argv[1] if len(sys.argv) > 1 else "meta/src/meta/grammar.y"
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    tokens, aliases, rules = parse_file(grammar_path)
    md = generate_markdown(tokens, aliases, rules)

    if output_path:
        Path(output_path).write_text(md)
        print(f"Written to {output_path}")
    else:
        print(md)


if __name__ == "__main__":
    main()
