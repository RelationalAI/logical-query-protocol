"""Common pretty printer generation logic shared across all target languages."""

from pathlib import Path
from typing import Any

from .codegen_base import CodeGenerator
from .dead_functions import live_functions
from .extra_pretty_gen import generate_extra_pretty_defs
from .grammar import Grammar
from .pretty_gen import generate_pretty_functions
from .proto_ast import ProtoEnum
from .target import EnumType, MessageType, PrintNonterminalDef


def _collect_dispatch_entries(
    defns: list[PrintNonterminalDef],
    codegen: CodeGenerator,
) -> dict[str, str]:
    """Collect type -> func_ref for grammar-based dispatch entries."""
    type_to_nonterminals: dict[str, list[tuple[str, str]]] = {}
    for defn in defns:
        type_str = codegen.gen_type(defn.nonterminal.type)
        func_ref = codegen.gen_pretty_nonterminal_ref(defn.nonterminal.name.lower())
        nt_name = defn.nonterminal.name
        if type_str not in type_to_nonterminals:
            type_to_nonterminals[type_str] = []
        type_to_nonterminals[type_str].append((nt_name, func_ref))

    result: dict[str, str] = {}
    for type_str, nonterminals in type_to_nonterminals.items():
        if len(nonterminals) == 1:
            _, func_ref = nonterminals[0]
        else:
            short_type = type_str.rsplit(".", 1)[-1].lower().replace("_", "")
            best = nonterminals[0]
            for nt_name, func_ref in nonterminals:
                if nt_name.lower().replace("_", "") == short_type:
                    best = (nt_name, func_ref)
                    break
            _, func_ref = best
        result[type_str] = func_ref
    return result


def _grammar_covered_types(
    defns: list[PrintNonterminalDef],
) -> set[tuple[str, str]]:
    """Collect (module, name) pairs for types covered by grammar rules."""
    covered: set[tuple[str, str]] = set()
    for defn in defns:
        t = defn.nonterminal.type
        if isinstance(t, MessageType):
            covered.add((t.module, t.name))
    return covered


def _generate_extra_printers(
    codegen: CodeGenerator,
    grammar_dispatch: dict[str, str],
    defns: list[PrintNonterminalDef],
    proto_messages: dict[tuple[str, str], Any] | None,
    proto_enums: dict[str, ProtoEnum] | None,
    indent: str,
) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Generate pretty printers for proto types not covered by grammar rules.

    Uses the target IR pipeline: builds PrintNonterminalDef nodes, then
    generates code via codegen.generate_def().

    Returns:
        (extra_defns_str, extra_msg_dispatch_entries, extra_enum_dispatch_entries)
    """
    extra_msg_dispatch: list[tuple[str, str]] = []
    extra_enum_dispatch: list[tuple[str, str]] = []

    if not proto_messages:
        return "", extra_msg_dispatch, extra_enum_dispatch

    covered = _grammar_covered_types(defns)
    # Also consider types already in grammar dispatch (covers parameterized types)
    for type_str in grammar_dispatch:
        # Try to reverse-map type strings that look like message types.
        # This is a heuristic for types the grammar covers via aliases.
        pass

    extra_defs = generate_extra_pretty_defs(proto_messages, proto_enums, covered)

    extra_lines: list[str] = []
    for defn in extra_defs:
        extra_lines.append("")
        extra_lines.append(codegen.generate_def(defn, indent))

        # Build dispatch entries from the definition's nonterminal type
        t = defn.nonterminal.type
        type_str = codegen.gen_type(t)
        func_ref = codegen.gen_pretty_nonterminal_ref(defn.nonterminal.name.lower())
        if isinstance(t, EnumType):
            extra_enum_dispatch.append((type_str, func_ref))
        else:
            extra_msg_dispatch.append((type_str, func_ref))

    return "\n".join(extra_lines), extra_msg_dispatch, extra_enum_dispatch


def generate_pretty_printer(
    grammar: Grammar,
    codegen: CodeGenerator,
    template_path: Path,
    command_line: str | None = None,
    proto_messages: dict[tuple[str, str], Any] | None = None,
    proto_enums: dict[str, ProtoEnum] | None = None,
) -> str:
    """Generate a pretty printer from a grammar using the given code generator and template."""
    template = template_path.read_text()
    indent = codegen.parse_def_indent

    defns = generate_pretty_functions(grammar)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, indent))
    lines.append("")
    pretty_nonterminal_defns = "\n".join(lines)

    live_funs = live_functions(
        [defn.body for defn in defns],
        grammar.function_defs,
    )

    function_lines = []
    for fundef in live_funs.values():
        function_lines.append("")
        function_lines.append(codegen.generate_method_def(fundef, indent))
    named_function_defns = "\n".join(function_lines) if function_lines else ""

    command_line_comment = (
        codegen.format_command_line_comment(command_line) if command_line else ""
    )

    # Collect grammar-based dispatch entries
    grammar_dispatch = _collect_dispatch_entries(defns, codegen)

    # Generate extra printers for uncovered types via IR
    extra_pretty_defns, extra_msg_dispatch, extra_enum_dispatch = (
        _generate_extra_printers(
            codegen,
            grammar_dispatch,
            defns,
            proto_messages,
            proto_enums,
            indent,
        )
    )

    # For Julia: generate per-method dispatch lines (existing pattern)
    pprint_dispatch_lines: list[str] = []
    for type_str, func_ref in grammar_dispatch.items():
        line = codegen.gen_pprint_dispatch_line(type_str, func_ref)
        if line is not None:
            pprint_dispatch_lines.append(line)
    for type_str, func_ref in extra_msg_dispatch:
        line = codegen.gen_pprint_dispatch_line(type_str, func_ref)
        if line is not None:
            pprint_dispatch_lines.append(line)
    for type_str, func_ref in extra_enum_dispatch:
        line = codegen.gen_pprint_dispatch_line(type_str, func_ref)
        if line is not None:
            pprint_dispatch_lines.append(line)
    pprint_dispatch_defns = "\n".join(pprint_dispatch_lines)

    # For Go/Python: generate dispatch function (Julia returns "" since it uses multiple dispatch)
    all_msg_entries = list(grammar_dispatch.items()) + extra_msg_dispatch
    dispatch_function = codegen.gen_dispatch_function(
        all_msg_entries, extra_enum_dispatch
    )

    format_kwargs = {
        "command_line_comment": command_line_comment,
        "start_name": grammar.start.name.lower(),
        "pretty_nonterminal_defns": pretty_nonterminal_defns,
        "named_function_defns": named_function_defns,
        "pprint_dispatch_defns": pprint_dispatch_defns,
        "extra_pretty_defns": extra_pretty_defns,
    }
    if "{dispatch_function}" in template:
        format_kwargs["dispatch_function"] = dispatch_function

    return template.format(**format_kwargs)
