"""Protobuf file parser.

This module provides a parser for protobuf (.proto) files, extracting
message and enum definitions.
"""

import re
from pathlib import Path
from typing import Dict

from .proto_ast import ProtoMessage, ProtoEnum, ProtoField, ProtoOneof


class ProtoParser:
    """Parser for protobuf files."""
    def __init__(self):
        self.messages: Dict[str, ProtoMessage] = {}
        self.enums: Dict[str, ProtoEnum] = {}

    def parse_file(self, filepath: Path) -> None:
        """Parse protobuf file and add messages/enums to internal state."""
        content = filepath.read_text()
        content = self._remove_comments(content)
        self._parse_content(content)

    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments."""
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content

    def _parse_content(self, content: str) -> None:
        """Parse message and enum definitions."""
        i = 0
        while i < len(content):
            message_match = re.match(r'message\s+(\w+)\s*\{', content[i:])
            if message_match:
                message_name = message_match.group(1)
                start = i + message_match.end()
                body, end = self._extract_braced_content(content, start)
                message = self._parse_message(message_name, body)
                self.messages[message_name] = message
                i = end
            else:
                enum_match = re.match(r'enum\s+(\w+)\s*\{', content[i:])
                if enum_match:
                    enum_name = enum_match.group(1)
                    start = i + enum_match.end()
                    body, end = self._extract_braced_content(content, start)
                    enum_obj = self._parse_enum(enum_name, body)
                    self.enums[enum_name] = enum_obj
                    i = end
                else:
                    i += 1

    def _extract_braced_content(self, content: str, start: int) -> tuple[str, int]:
        """Extract content within matching braces, handling nested braces."""
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
            i += 1
        return content[start:i-1], i

    def _parse_message(self, name: str, body: str) -> ProtoMessage:
        """Parse message definition body into fields, oneofs, and nested enums."""
        message = ProtoMessage(name=name)

        oneof_pattern = r'oneof\s+(\w+)\s*\{((?:[^{}]|\{[^}]*\})*)\}'
        oneofs = {}
        for match in re.finditer(oneof_pattern, body):
            oneof_name = match.group(1)
            oneof_body = match.group(2)
            oneof = ProtoOneof(name=oneof_name)
            oneofs[oneof_name] = oneof
            message.oneofs.append(oneof)

            for field_match in re.finditer(r'(\w+)\s+(\w+)\s*=\s*(\d+);', oneof_body):
                field_type = field_match.group(1)
                field_name = field_match.group(2)
                field_number = int(field_match.group(3))
                proto_field = ProtoField(
                    name=field_name,
                    type=field_type,
                    number=field_number
                )
                oneof.fields.append(proto_field)

        field_pattern = r'(repeated|optional)?\s*(\w+)\s+(\w+)\s*=\s*(\d+);'
        for match in re.finditer(field_pattern, body):
            if any(match.start() >= m.start() and match.end() <= m.end()
                   for m in re.finditer(oneof_pattern, body)):
                continue

            modifier = match.group(1)
            field_type = match.group(2)
            field_name = match.group(3)
            field_number = int(match.group(4))

            if field_type == 'reserved':
                continue

            proto_field = ProtoField(
                name=field_name,
                type=field_type,
                number=field_number,
                is_repeated=modifier == 'repeated',
                is_optional=modifier == 'optional'
            )
            message.fields.append(proto_field)

        enum_pattern = r'enum\s+(\w+)\s*\{([^}]+)\}'
        for match in re.finditer(enum_pattern, body):
            enum_name = match.group(1)
            enum_body = match.group(2)
            enum_obj = self._parse_enum(enum_name, enum_body)
            message.enums.append(enum_obj)

        return message

    def _parse_enum(self, name: str, body: str) -> ProtoEnum:
        """Parse enum definition body into values."""
        enum_obj = ProtoEnum(name=name)
        for match in re.finditer(r'(\w+)\s*=\s*(\d+);', body):
            value_name = match.group(1)
            value_number = int(match.group(2))
            enum_obj.values.append((value_name, value_number))
        return enum_obj
