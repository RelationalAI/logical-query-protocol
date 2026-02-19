"""Common pretty printer generation logic shared across all target languages."""

from pathlib import Path

from .codegen_base import CodeGenerator
from .dead_functions import live_functions
from .grammar import Grammar
from .pretty_gen import generate_pretty_functions
from .target import PrintNonterminalDef


def _generate_pprint_dispatch(
    defns: list[PrintNonterminalDef],
    codegen: CodeGenerator,
) -> str:
    """Generate _pprint_dispatch methods that dispatch on protobuf type.

    For each unique protobuf type among the nonterminal definitions, generate
    a _pprint_dispatch(pp, x::Type) method that calls the appropriate
    pretty_<nonterminal> function.

    When multiple nonterminals target the same type, prefer the one whose
    name (minus underscores, lowered) matches the type's short name (lowered).
    """
    # Collect type -> list of (nonterminal_name, function_ref) pairs
    type_to_nonterminals: dict[str, list[tuple[str, str]]] = {}
    for defn in defns:
        type_str = codegen.gen_type(defn.nonterminal.type)
        func_ref = codegen.gen_pretty_nonterminal_ref(defn.nonterminal.name.lower())
        nt_name = defn.nonterminal.name
        if type_str not in type_to_nonterminals:
            type_to_nonterminals[type_str] = []
        type_to_nonterminals[type_str].append((nt_name, func_ref))

    lines: list[str] = []
    for type_str, nonterminals in type_to_nonterminals.items():
        if len(nonterminals) == 1:
            _, func_ref = nonterminals[0]
        else:
            # Prefer the nonterminal whose name matches the type's short name.
            # E.g., for Proto.Conjunction prefer "conjunction" over "true".
            short_type = type_str.rsplit(".", 1)[-1].lower().replace("_", "")
            best = nonterminals[0]
            for nt_name, func_ref in nonterminals:
                if nt_name.lower().replace("_", "") == short_type:
                    best = (nt_name, func_ref)
                    break
            _, func_ref = best
        lines.append(
            f"_pprint_dispatch(pp::PrettyPrinter, x::{type_str}) = {func_ref}(pp, x)"
        )

    return "\n".join(lines)


def generate_pretty_printer(
    grammar: Grammar,
    codegen: CodeGenerator,
    template_path: Path,
    command_line: str | None = None,
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

    pprint_dispatch_defns = _generate_pprint_dispatch(defns, codegen)

    return template.format(
        command_line_comment=command_line_comment,
        start_name=grammar.start.name.lower(),
        pretty_nonterminal_defns=pretty_nonterminal_defns,
        named_function_defns=named_function_defns,
        pprint_dispatch_defns=pprint_dispatch_defns,
    )
