"""Protobuf message and enum formatting utilities."""


def format_message(msg, indent=0):
    """Format a ProtoMessage for display."""
    prefix = "  " * indent
    lines = [f"{prefix}message {msg.name} {{"]

    for enum in msg.enums:
        lines.append(f"{prefix}  enum {enum.name} {{")
        for value_name, value_number in enum.values:
            lines.append(f"{prefix}    {value_name} = {value_number};")
        lines.append(f"{prefix}  }}")

    for oneof in msg.oneofs:
        lines.append(f"{prefix}  oneof {oneof.name} {{")
        for field in oneof.fields:
            lines.append(f"{prefix}    {field.type} {field.name} = {field.number};")
        lines.append(f"{prefix}  }}")

    for field in msg.fields:
        modifiers = []
        if field.is_repeated:
            modifiers.append("repeated")
        if field.is_optional:
            modifiers.append("optional")
        modifier_str = " ".join(modifiers) + " " if modifiers else ""
        lines.append(
            f"{prefix}  {modifier_str}{field.type} {field.name} = {field.number};"
        )

    lines.append(f"{prefix}}}")
    return "\n".join(lines)


def format_enum(enum, indent=0):
    """Format a ProtoEnum for display."""
    prefix = "  " * indent
    lines = [f"{prefix}enum {enum.name} {{"]
    for value_name, value_number in enum.values:
        lines.append(f"{prefix}  {value_name} = {value_number};")
    lines.append(f"{prefix}}}")
    return "\n".join(lines)


def print_proto_spec(proto_parser):
    """Format a ProtoParser's parsed specification for display.

    Args:
        proto_parser: ProtoParser instance with parsed messages and enums

    Returns:
        Formatted string representation of all messages and enums
    """
    lines = []
    for msg_name, msg in sorted(proto_parser.messages.items()):
        lines.append(format_message(msg))
        lines.append("")

    for enum_name, enum in sorted(proto_parser.enums.items()):
        lines.append(format_enum(enum))
        lines.append("")

    return "\n".join(lines)
