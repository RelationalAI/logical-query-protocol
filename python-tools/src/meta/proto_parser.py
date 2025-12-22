"""Protobuf file parser.

This module provides a parser for protobuf (.proto) files, extracting
message and enum definitions.
"""

import re
from pathlib import Path
from typing import Dict

from .proto_ast import ProtoMessage, ProtoEnum, ProtoField, ProtoOneof, ProtoReserved

# Regex patterns for parsing protobuf syntax
_LINE_COMMENT_PATTERN = re.compile(r'//.*?\n')
_BLOCK_COMMENT_PATTERN = re.compile(r'/\*.*?\*/', re.DOTALL)
_MESSAGE_PATTERN = re.compile(r'message\s+(\w+)\s*\{')
_ENUM_PATTERN = re.compile(r'enum\s+(\w+)\s*\{')
_NESTED_ENUM_PATTERN = re.compile(r'enum\s+(\w+)\s*\{([^}]+)\}')
_ONEOF_PATTERN = re.compile(r'oneof\s+(\w+)\s*\{((?:[^{}]|\{[^}]*\})*)\}')
_FIELD_PATTERN = re.compile(r'(repeated|optional)?\s*(\w+)\s+(\w+)\s*=\s*(\d+);')
_ONEOF_FIELD_PATTERN = re.compile(r'(\w+)\s+(\w+)\s*=\s*(\d+);')
_ENUM_VALUE_PATTERN = re.compile(r'(\w+)\s*=\s*(\d+);')
_RESERVED_PATTERN = re.compile(r'reserved\s+([^;]+);')


class ProtoParser:
    """Parser for protobuf files."""
    def __init__(self):
        self.messages: Dict[str, ProtoMessage] = {}
        self.enums: Dict[str, ProtoEnum] = {}
        self.current_module: str = ""

    def parse_file(self, filepath: Path) -> None:
        """Parse protobuf file and add messages/enums to internal state."""
        self.current_module = filepath.stem
        content = filepath.read_text()
        content = self._remove_comments(content)
        self._parse_content(content)

    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments."""
        content = _LINE_COMMENT_PATTERN.sub('\n', content)
        content = _BLOCK_COMMENT_PATTERN.sub('', content)
        return content

    def _parse_content(self, content: str) -> None:
        """Parse message and enum definitions."""
        i = 0
        while i < len(content):
            message_match = _MESSAGE_PATTERN.match(content, i)
            if message_match:
                message_name = message_match.group(1)
                start = message_match.end()
                body, end = self._extract_braced_content(content, start)
                message = self._parse_message(message_name, body)
                self.messages[message_name] = message
                i = end
            else:
                enum_match = _ENUM_PATTERN.match(content, i)
                if enum_match:
                    enum_name = enum_match.group(1)
                    start = enum_match.end()
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

    def _parse_reserved(self, content: str) -> ProtoReserved:
        """Parse reserved statement content into numbers, ranges, and names."""
        reserved = ProtoReserved()
        parts = [p.strip() for p in content.split(',')]

        for part in parts:
            if '"' in part:
                name = part.strip('"').strip("'")
                reserved.names.append(name)
            elif ' to ' in part:
                range_parts = part.split(' to ')
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
                reserved.ranges.append((start, end))
            else:
                reserved.numbers.append(int(part.strip()))

        return reserved

    def _parse_message(self, name: str, body: str) -> ProtoMessage:
        """Parse message definition body into fields, oneofs, and nested enums."""
        message = ProtoMessage(name=name, module=self.current_module)

        # Parse oneofs and track their spans
        oneof_spans = []
        for match in _ONEOF_PATTERN.finditer(body):
            oneof_spans.append((match.start(), match.end()))
            oneof_name = match.group(1)
            oneof_body = match.group(2)
            oneof = ProtoOneof(name=oneof_name)
            message.oneofs.append(oneof)

            for field_match in _ONEOF_FIELD_PATTERN.finditer(oneof_body):
                field_type = field_match.group(1)
                field_name = field_match.group(2)
                field_number = int(field_match.group(3))
                proto_field = ProtoField(
                    name=field_name,
                    type=field_type,
                    number=field_number
                )
                oneof.fields.append(proto_field)

        # Parse reserved statements and track their spans
        reserved_spans = []
        for match in _RESERVED_PATTERN.finditer(body):
            reserved_spans.append((match.start(), match.end()))
            reserved_content = match.group(1)
            reserved = self._parse_reserved(reserved_content)
            message.reserved.append(reserved)

        # Parse regular fields (excluding those inside oneofs and reserved)
        excluded_spans = oneof_spans + reserved_spans
        for match in _FIELD_PATTERN.finditer(body):
            if any(start <= match.start() and match.end() <= end
                   for start, end in excluded_spans):
                continue

            modifier = match.group(1)
            field_type = match.group(2)
            field_name = match.group(3)
            field_number = int(match.group(4))

            proto_field = ProtoField(
                name=field_name,
                type=field_type,
                number=field_number,
                is_repeated=modifier == 'repeated',
                is_optional=modifier == 'optional'
            )
            message.fields.append(proto_field)

        # Parse nested enums
        for match in _NESTED_ENUM_PATTERN.finditer(body):
            enum_name = match.group(1)
            enum_body = match.group(2)
            enum_obj = self._parse_enum(enum_name, enum_body)
            message.enums.append(enum_obj)

        return message

    def _parse_enum(self, name: str, body: str) -> ProtoEnum:
        """Parse enum definition body into values."""
        enum_obj = ProtoEnum(name=name)
        for match in _ENUM_VALUE_PATTERN.finditer(body):
            value_name = match.group(1)
            value_number = int(match.group(2))
            enum_obj.values.append((value_name, value_number))
        return enum_obj
