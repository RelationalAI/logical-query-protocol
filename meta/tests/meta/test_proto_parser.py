"""Tests for protobuf parser."""

import unittest
from pathlib import Path
import tempfile
import shutil

from meta.proto_parser import ProtoParser


class TestProtoParser(unittest.TestCase):
    """Test cases for ProtoParser."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_dir_path = Path(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_parse_simple_message(self):
        """Test parsing a simple message with basic fields."""
        proto_content = """
        syntax = "proto3";

        message Person {
          string name = 1;
          int32 age = 2;
          bool active = 3;
        }
        """
        proto_file = self.test_dir_path / "simple.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        self.assertIn("Person", parser.messages)
        msg = parser.messages["Person"]
        self.assertEqual(msg.name, "Person")
        self.assertEqual(msg.module, "simple")
        self.assertEqual(len(msg.fields), 3)

        self.assertEqual(msg.fields[0].name, "name")
        self.assertEqual(msg.fields[0].type, "string")
        self.assertEqual(msg.fields[0].number, 1)
        self.assertFalse(msg.fields[0].is_repeated)
        self.assertFalse(msg.fields[0].is_optional)

        self.assertEqual(msg.fields[1].name, "age")
        self.assertEqual(msg.fields[1].type, "int32")
        self.assertEqual(msg.fields[1].number, 2)

        self.assertEqual(msg.fields[2].name, "active")
        self.assertEqual(msg.fields[2].type, "bool")
        self.assertEqual(msg.fields[2].number, 3)

    def test_parse_repeated_fields(self):
        """Test parsing repeated fields."""
        proto_content = """
        message Container {
          repeated string items = 1;
          repeated int32 numbers = 2;
        }
        """
        proto_file = self.test_dir_path / "repeated.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["Container"]
        self.assertEqual(len(msg.fields), 2)
        self.assertTrue(msg.fields[0].is_repeated)
        self.assertTrue(msg.fields[1].is_repeated)

    def test_parse_optional_fields(self):
        """Test parsing optional fields."""
        proto_content = """
        message OptionalFields {
          optional string description = 1;
          optional int32 count = 2;
        }
        """
        proto_file = self.test_dir_path / "optional.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["OptionalFields"]
        self.assertEqual(len(msg.fields), 2)
        self.assertTrue(msg.fields[0].is_optional)
        self.assertTrue(msg.fields[1].is_optional)

    def test_parse_oneof(self):
        """Test parsing oneof groups."""
        proto_content = """
        message TestOneof {
          oneof test_oneof {
            string name = 1;
            int32 id = 2;
            bool flag = 3;
          }
        }
        """
        proto_file = self.test_dir_path / "oneof.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["TestOneof"]
        self.assertEqual(len(msg.oneofs), 1)
        oneof = msg.oneofs[0]
        self.assertEqual(oneof.name, "test_oneof")
        self.assertEqual(len(oneof.fields), 3)

        self.assertEqual(oneof.fields[0].name, "name")
        self.assertEqual(oneof.fields[0].type, "string")
        self.assertEqual(oneof.fields[0].number, 1)

        self.assertEqual(oneof.fields[1].name, "id")
        self.assertEqual(oneof.fields[1].type, "int32")
        self.assertEqual(oneof.fields[1].number, 2)

        self.assertEqual(oneof.fields[2].name, "flag")
        self.assertEqual(oneof.fields[2].type, "bool")
        self.assertEqual(oneof.fields[2].number, 3)

    def test_parse_nested_enum(self):
        """Test parsing nested enums."""
        proto_content = """
        message MessageWithEnum {
          enum Status {
            UNKNOWN = 0;
            ACTIVE = 1;
            INACTIVE = 2;
          }
          Status status = 1;
        }
        """
        proto_file = self.test_dir_path / "nested_enum.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["MessageWithEnum"]
        self.assertEqual(len(msg.enums), 1)
        enum = msg.enums[0]
        self.assertEqual(enum.name, "Status")
        self.assertEqual(len(enum.values), 3)

        self.assertEqual(enum.values[0], ("UNKNOWN", 0))
        self.assertEqual(enum.values[1], ("ACTIVE", 1))
        self.assertEqual(enum.values[2], ("INACTIVE", 2))

        self.assertEqual(len(msg.fields), 1)
        self.assertEqual(msg.fields[0].name, "status")
        self.assertEqual(msg.fields[0].type, "Status")

    def test_parse_top_level_enum(self):
        """Test parsing top-level enums."""
        proto_content = """
        enum Color {
          RED = 0;
          GREEN = 1;
          BLUE = 2;
        }
        """
        proto_file = self.test_dir_path / "enum.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        self.assertIn("Color", parser.enums)
        enum = parser.enums["Color"]
        self.assertEqual(enum.name, "Color")
        self.assertEqual(len(enum.values), 3)
        self.assertEqual(enum.values[0], ("RED", 0))
        self.assertEqual(enum.values[1], ("GREEN", 1))
        self.assertEqual(enum.values[2], ("BLUE", 2))

    def test_parse_comments(self):
        """Test that comments are properly removed."""
        proto_content = """
        // This is a line comment
        message CommentTest {
          /* This is a block comment */
          string field1 = 1; // inline comment
          /* Multi-line
             block comment */
          int32 field2 = 2;
        }
        """
        proto_file = self.test_dir_path / "comments.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["CommentTest"]
        self.assertEqual(len(msg.fields), 2)
        self.assertEqual(msg.fields[0].name, "field1")
        self.assertEqual(msg.fields[1].name, "field2")

    def test_parse_multiple_messages(self):
        """Test parsing multiple messages in a file."""
        proto_content = """
        message Message1 {
          string field1 = 1;
        }

        message Message2 {
          int32 field2 = 1;
        }

        message Message3 {
          bool field3 = 1;
        }
        """
        proto_file = self.test_dir_path / "multiple.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        self.assertEqual(len(parser.messages), 3)
        self.assertIn("Message1", parser.messages)
        self.assertIn("Message2", parser.messages)
        self.assertIn("Message3", parser.messages)

    def test_parse_complex_message(self):
        """Test parsing a complex message with multiple features."""
        proto_content = """
        message ComplexMessage {
          enum Priority {
            LOW = 0;
            MEDIUM = 1;
            HIGH = 2;
          }

          string name = 1;
          repeated int32 ids = 2;
          optional string description = 3;

          oneof kind {
            string text = 4;
            int32 number = 5;
          }

          Priority priority = 6;
        }
        """
        proto_file = self.test_dir_path / "complex.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ComplexMessage"]
        self.assertEqual(len(msg.enums), 1)
        self.assertEqual(len(msg.fields), 4)
        self.assertEqual(len(msg.oneofs), 1)

        self.assertEqual(msg.fields[0].name, "name")
        self.assertFalse(msg.fields[0].is_repeated)

        self.assertEqual(msg.fields[1].name, "ids")
        self.assertTrue(msg.fields[1].is_repeated)

        self.assertEqual(msg.fields[2].name, "description")
        self.assertTrue(msg.fields[2].is_optional)

        self.assertEqual(msg.fields[3].name, "priority")
        self.assertEqual(msg.fields[3].type, "Priority")

        self.assertEqual(msg.oneofs[0].name, "kind")
        self.assertEqual(len(msg.oneofs[0].fields), 2)

    def test_parse_multiple_files(self):
        """Test parsing multiple proto files."""
        proto1 = self.test_dir_path / "file1.proto"
        proto1.write_text("message Message1 { string field = 1; }")

        proto2 = self.test_dir_path / "file2.proto"
        proto2.write_text("message Message2 { int32 field = 1; }")

        parser = ProtoParser()
        parser.parse_file(proto1)
        parser.parse_file(proto2)

        self.assertEqual(len(parser.messages), 2)
        self.assertIn("Message1", parser.messages)
        self.assertIn("Message2", parser.messages)
        self.assertEqual(parser.messages["Message1"].module, "file1")
        self.assertEqual(parser.messages["Message2"].module, "file2")

    def test_parse_reserved_single_number(self):
        """Test parsing reserved with a single field number."""
        proto_content = """
        message ReservedTest {
          reserved 4;
          string name = 1;
          int32 id = 2;
        }
        """
        proto_file = self.test_dir_path / "reserved_single.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 1)
        self.assertEqual(msg.reserved[0].numbers, [4])
        self.assertEqual(msg.reserved[0].ranges, [])
        self.assertEqual(msg.reserved[0].names, [])
        self.assertEqual(len(msg.fields), 2)

    def test_parse_reserved_multiple_numbers(self):
        """Test parsing reserved with multiple field numbers."""
        proto_content = """
        message ReservedTest {
          reserved 2, 3, 5;
          string name = 1;
          int32 id = 4;
        }
        """
        proto_file = self.test_dir_path / "reserved_multiple.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 1)
        self.assertEqual(msg.reserved[0].numbers, [2, 3, 5])
        self.assertEqual(msg.reserved[0].ranges, [])
        self.assertEqual(msg.reserved[0].names, [])

    def test_parse_reserved_range(self):
        """Test parsing reserved with a field number range."""
        proto_content = """
        message ReservedTest {
          reserved 9 to 11;
          string name = 1;
          int32 id = 2;
        }
        """
        proto_file = self.test_dir_path / "reserved_range.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 1)
        self.assertEqual(msg.reserved[0].numbers, [])
        self.assertEqual(msg.reserved[0].ranges, [(9, 11)])
        self.assertEqual(msg.reserved[0].names, [])

    def test_parse_reserved_names(self):
        """Test parsing reserved with field names."""
        proto_content = """
        message ReservedTest {
          reserved "foo", "bar";
          string name = 1;
          int32 id = 2;
        }
        """
        proto_file = self.test_dir_path / "reserved_names.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 1)
        self.assertEqual(msg.reserved[0].numbers, [])
        self.assertEqual(msg.reserved[0].ranges, [])
        self.assertEqual(msg.reserved[0].names, ["foo", "bar"])

    def test_parse_reserved_mixed(self):
        """Test parsing reserved with mixed numbers and ranges."""
        proto_content = """
        message ReservedTest {
          reserved 2, 9 to 11, 15;
          string name = 1;
          int32 id = 3;
        }
        """
        proto_file = self.test_dir_path / "reserved_mixed.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 1)
        self.assertEqual(msg.reserved[0].numbers, [2, 15])
        self.assertEqual(msg.reserved[0].ranges, [(9, 11)])
        self.assertEqual(msg.reserved[0].names, [])

    def test_parse_reserved_with_oneof(self):
        """Test parsing reserved in a message with oneof."""
        proto_content = """
        message ReservedTest {
          reserved 4;
          string name = 1;
          oneof kind {
            string text = 2;
            int32 number = 3;
          }
          int32 id = 5;
        }
        """
        proto_file = self.test_dir_path / "reserved_oneof.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 1)
        self.assertEqual(msg.reserved[0].numbers, [4])
        self.assertEqual(len(msg.fields), 2)
        self.assertEqual(len(msg.oneofs), 1)
        self.assertEqual(len(msg.oneofs[0].fields), 2)

    def test_parse_reserved_multiple_statements(self):
        """Test parsing multiple reserved statements."""
        proto_content = """
        message ReservedTest {
          reserved 2, 3;
          reserved 9 to 11;
          reserved "foo", "bar";
          string name = 1;
          int32 id = 4;
        }
        """
        proto_file = self.test_dir_path / "reserved_multi_stmt.proto"
        proto_file.write_text(proto_content)

        parser = ProtoParser()
        parser.parse_file(proto_file)

        msg = parser.messages["ReservedTest"]
        self.assertEqual(len(msg.reserved), 3)
        self.assertEqual(msg.reserved[0].numbers, [2, 3])
        self.assertEqual(msg.reserved[1].ranges, [(9, 11)])
        self.assertEqual(msg.reserved[2].names, ["foo", "bar"])
