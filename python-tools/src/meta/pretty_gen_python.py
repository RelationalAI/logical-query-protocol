"""Python-specific pretty printer code generation.

Generates pretty printers in Python from grammars. Handles Python-specific
code generation including prologue (imports, PrettyPrinter class), pretty
print method generation, and epilogue.
"""

from typing import Optional

from .grammar import Grammar, Nonterminal
from .codegen_python import PythonCodeGenerator
from .pretty_gen import generate_pretty_functions


PROLOGUE_TEMPLATE = '''\
"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.

{command_line_comment}"""

from io import StringIO
from typing import Any, IO, Never, Optional

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: Optional[IO[str]] = None):
        self.io = io if io is not None else StringIO()
        self.indent_level = 0
        self.at_line_start = True
        self._debug_info: dict[tuple[int, int], str] = {{}}

    def write(self, s: str) -> None:
        """Write a string to the output, with indentation at line start."""
        if self.at_line_start and s.strip():
            self.io.write('  ' * self.indent_level)
            self.at_line_start = False
        self.io.write(s)

    def newline(self) -> None:
        """Write a newline to the output."""
        self.io.write('\\n')
        self.at_line_start = True

    def indent(self, delta: int = 1) -> None:
        """Increase indentation level."""
        self.indent_level += delta

    def dedent(self, delta: int = 1) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - delta)

    def get_output(self) -> str:
        """Get the accumulated output as a string."""
        if isinstance(self.io, StringIO):
            return self.io.getvalue()
        return ""

    def format_decimal(self, msg) -> str:
        """Format a DecimalValue protobuf message as a string."""
        # DecimalValue has 'value' field as string
        return str(msg.value) if msg.value else "0"

    def format_int128(self, msg) -> str:
        """Format an Int128Value protobuf message as a string."""
        value = (msg.high << 64) | msg.low
        if msg.high & (1 << 63):
            value -= (1 << 128)
        return str(value)

    def format_uint128(self, msg) -> str:
        """Format a UInt128Value protobuf message as a hex string."""
        value = (msg.high << 64) | msg.low
        return f"0x{{value:032x}}"

    def fragment_id_to_string(self, msg) -> str:
        """Convert FragmentId to string representation."""
        return msg.id.decode('utf-8') if msg.id else ""

    def start_pretty_fragment(self, msg) -> None:
        """Extract debug info from Fragment for relation ID lookup."""
        debug_info = msg.debug_info
        for rid, name in zip(debug_info.ids, debug_info.orig_names):
            self._debug_info[(rid.id_low, rid.id_high)] = name

    def relation_id_to_string(self, msg) -> str:
        """Convert RelationId to string representation using debug info."""
        return self._debug_info.get((msg.id_low, msg.id_high), "")

    def relation_id_to_int(self, msg):
        """Convert RelationId to int representation if it has id."""
        if msg.id_low or msg.id_high:
            return (msg.id_high << 64) | msg.id_low
        return None

    def relation_id_to_uint128(self, msg):
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)
'''

EPILOGUE_TEMPLATE = '''

def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_{start_name}(msg)
    return printer.get_output()
'''


def generate_pretty_printer_python(grammar: Grammar, command_line: Optional[str] = None,
                                   proto_messages=None) -> str:
    """Generate pretty printer in Python."""
    prologue = _generate_prologue(command_line)

    codegen = PythonCodeGenerator(proto_messages=proto_messages)
    codegen.named_fun_class = "self"

    defns = generate_pretty_functions(grammar, proto_messages)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, "    "))

    for fundef in grammar.function_defs.values():
        lines.append("")
        lines.append(codegen.generate_method_def(fundef, "    "))
    lines.append("")

    epilogue = _generate_epilogue(grammar.start)

    return prologue + "\n".join(lines) + epilogue


def _generate_prologue(command_line: Optional[str] = None) -> str:
    """Generate pretty printer prologue with imports and class start."""
    command_line_comment = f"\nCommand: {command_line}\n" if command_line else ""
    return PROLOGUE_TEMPLATE.format(command_line_comment=command_line_comment)


def _generate_epilogue(start: Nonterminal) -> str:
    """Generate pretty function."""
    return EPILOGUE_TEMPLATE.format(start_name=start.name.lower())
