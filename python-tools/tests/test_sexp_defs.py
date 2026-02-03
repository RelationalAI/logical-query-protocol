"""Unit tests for function definitions in grammar.sexp.

Tests the IR-defined functions (_extract_value_*, construct_*, export_*)
that are generated from the (def ...) declarations in grammar.sexp.
"""

import pytest
from lqp.proto.v1 import logic_pb2, transactions_pb2
from lqp.generated_parser import Parser


class TestExtractValueFunctions:
    """Tests for _extract_value_* functions."""

    def test_extract_value_int64_with_value(self):
        """Test _extract_value_int64 extracts int from Value message."""
        value = logic_pb2.Value(int_value=42)
        result = Parser._extract_value_int64(value, 0)
        assert result == 42

    def test_extract_value_int64_with_none(self):
        """Test _extract_value_int64 returns default when value is None."""
        result = Parser._extract_value_int64(None, 99)
        assert result == 99

    def test_extract_value_int64_with_wrong_field(self):
        """Test _extract_value_int64 returns default when wrong field is set."""
        value = logic_pb2.Value(string_value="not an int")
        result = Parser._extract_value_int64(value, 99)
        assert result == 99

    def test_extract_value_float64_with_value(self):
        """Test _extract_value_float64 extracts float from Value message."""
        value = logic_pb2.Value(float_value=3.14)
        result = Parser._extract_value_float64(value, 0.0)
        assert result == 3.14

    def test_extract_value_float64_with_none(self):
        """Test _extract_value_float64 returns default when value is None."""
        result = Parser._extract_value_float64(None, 2.71)
        assert result == 2.71

    def test_extract_value_string_with_value(self):
        """Test _extract_value_string extracts string from Value message."""
        value = logic_pb2.Value(string_value="hello")
        result = Parser._extract_value_string(value, "")
        assert result == "hello"

    def test_extract_value_string_with_none(self):
        """Test _extract_value_string returns default when value is None."""
        result = Parser._extract_value_string(None, "default")
        assert result == "default"

    def test_extract_value_boolean_with_true(self):
        """Test _extract_value_boolean extracts True from Value message."""
        value = logic_pb2.Value(boolean_value=True)
        result = Parser._extract_value_boolean(value, False)
        assert result is True

    def test_extract_value_boolean_with_false(self):
        """Test _extract_value_boolean extracts False from Value message."""
        value = logic_pb2.Value(boolean_value=False)
        result = Parser._extract_value_boolean(value, True)
        assert result is False

    def test_extract_value_boolean_with_none(self):
        """Test _extract_value_boolean returns default when value is None."""
        result = Parser._extract_value_boolean(None, True)
        assert result is True

    def test_extract_value_bytes_with_string(self):
        """Test _extract_value_bytes encodes string from Value message."""
        value = logic_pb2.Value(string_value="test data")
        result = Parser._extract_value_bytes(value, b"default")
        assert result == b"test data"

    def test_extract_value_bytes_with_none(self):
        """Test _extract_value_bytes returns default when value is None."""
        result = Parser._extract_value_bytes(None, b"default")
        assert result == b"default"

    def test_extract_value_bytes_with_wrong_field(self):
        """Test _extract_value_bytes returns default when wrong field is set."""
        value = logic_pb2.Value(int_value=42)
        result = Parser._extract_value_bytes(value, b"default")
        assert result == b"default"

    def test_extract_value_uint128_with_value(self):
        """Test _extract_value_uint128 extracts UInt128Value from Value message."""
        uint128 = logic_pb2.UInt128Value(low=123, high=456)
        value = logic_pb2.Value(uint128_value=uint128)
        default = logic_pb2.UInt128Value(low=0, high=0)
        result = Parser._extract_value_uint128(value, default)
        assert result.low == 123
        assert result.high == 456

    def test_extract_value_uint128_with_none(self):
        """Test _extract_value_uint128 returns default when value is None."""
        default = logic_pb2.UInt128Value(low=999, high=888)
        result = Parser._extract_value_uint128(None, default)
        assert result.low == 999
        assert result.high == 888

    def test_extract_value_string_list_with_value(self):
        """Test _extract_value_string_list extracts list from Value message."""
        value = logic_pb2.Value(string_value="test")
        result = Parser._extract_value_string_list(value, [])
        assert result == ["test"]

    def test_extract_value_string_list_with_none(self):
        """Test _extract_value_string_list returns default when value is None."""
        result = Parser._extract_value_string_list(None, ["default"])
        assert result == ["default"]


class TestConstructCSVConfig:
    """Tests for construct_csv_config function."""

    def test_construct_csv_config_with_defaults(self):
        """Test construct_csv_config with empty config uses defaults."""
        config_dict = []
        result = Parser.construct_csv_config(config_dict)

        assert result.header_row == 1
        assert result.skip == 0
        assert result.new_line == ""
        assert result.delimiter == ","
        assert result.quotechar == "\""
        assert result.escapechar == "\""
        assert result.comment == ""
        assert list(result.missing_strings) == []
        assert result.decimal_separator == "."
        assert result.encoding == "utf-8"
        assert result.compression == "auto"

    def test_construct_csv_config_with_custom_values(self):
        """Test construct_csv_config with custom values."""
        config_dict = [
            ("csv_header_row", logic_pb2.Value(int_value=2)),
            ("csv_skip", logic_pb2.Value(int_value=5)),
            ("csv_delimiter", logic_pb2.Value(string_value="|")),
            ("csv_encoding", logic_pb2.Value(string_value="latin-1")),
        ]
        result = Parser.construct_csv_config(config_dict)

        assert result.header_row == 2
        assert result.skip == 5
        assert result.delimiter == "|"
        assert result.encoding == "latin-1"
        # Unspecified values use defaults
        assert result.quotechar == "\""
        assert result.compression == "auto"


class TestConstructBeTreeInfo:
    """Tests for construct_betree_info function."""

    def test_construct_betree_info_with_root_pageid(self):
        """Test construct_betree_info with root_pageid (not inline_data)."""
        uint128 = logic_pb2.UInt128Value(low=123, high=456)
        config_dict = [
            ("betree_config_epsilon", logic_pb2.Value(float_value=0.7)),
            ("betree_locator_root_pageid", logic_pb2.Value(uint128_value=uint128)),
            ("betree_locator_element_count", logic_pb2.Value(int_value=100)),
        ]
        key_types = [logic_pb2.Type(int_type=logic_pb2.IntType())]
        value_types = [logic_pb2.Type(string_type=logic_pb2.StringType())]

        result = Parser.construct_betree_info(key_types, value_types, config_dict)

        assert result.storage_config.epsilon == 0.7
        assert result.storage_config.max_pivots == 4  # default
        assert result.relation_locator.HasField("root_pageid")
        assert result.relation_locator.root_pageid.low == 123
        assert result.relation_locator.root_pageid.high == 456
        assert not result.relation_locator.HasField("inline_data")
        assert result.relation_locator.element_count == 100

    def test_construct_betree_info_with_inline_data(self):
        """Test construct_betree_info with inline_data (not root_pageid)."""
        config_dict = [
            ("betree_locator_inline_data", logic_pb2.Value(string_value="binary data")),
            ("betree_locator_element_count", logic_pb2.Value(int_value=42)),
        ]
        key_types = []
        value_types = []

        result = Parser.construct_betree_info(key_types, value_types, config_dict)

        assert result.relation_locator.HasField("inline_data")
        assert result.relation_locator.inline_data == b"binary data"
        assert not result.relation_locator.HasField("root_pageid")
        assert result.relation_locator.element_count == 42

    def test_construct_betree_info_with_defaults(self):
        """Test construct_betree_info with empty config uses defaults."""
        result = Parser.construct_betree_info([], [], [])

        assert result.storage_config.epsilon == 0.5
        assert result.storage_config.max_pivots == 4
        assert result.storage_config.max_deltas == 16
        assert result.storage_config.max_leaf == 16
        assert result.relation_locator.element_count == 0
        assert result.relation_locator.tree_height == 0


class TestConstructConfigure:
    """Tests for construct_configure function."""

    def test_construct_configure_with_default_level(self):
        """Test construct_configure with no maintenance level uses default."""
        config_dict = [
            ("semantics_version", logic_pb2.Value(int_value=2)),
        ]
        result = Parser.construct_configure(config_dict)

        assert result.semantics_version == 2
        # level is an enum, value 1 = MAINTENANCE_LEVEL_OFF
        assert result.ivm_config.level == transactions_pb2.MAINTENANCE_LEVEL_OFF

    def test_construct_configure_with_off_level(self):
        """Test construct_configure with OFF maintenance level."""
        config_dict = [
            ("semantics_version", logic_pb2.Value(int_value=1)),
            ("ivm.maintenance_level", logic_pb2.Value(string_value="off")),
        ]
        result = Parser.construct_configure(config_dict)

        assert result.semantics_version == 1
        assert result.ivm_config.level == transactions_pb2.MAINTENANCE_LEVEL_OFF

    def test_construct_configure_with_auto_level(self):
        """Test construct_configure with AUTO maintenance level."""
        config_dict = [
            ("ivm.maintenance_level", logic_pb2.Value(string_value="auto")),
        ]
        result = Parser.construct_configure(config_dict)

        assert result.ivm_config.level == transactions_pb2.MAINTENANCE_LEVEL_AUTO

    def test_construct_configure_with_all_level(self):
        """Test construct_configure with ALL maintenance level."""
        config_dict = [
            ("ivm.maintenance_level", logic_pb2.Value(string_value="ALL")),
        ]
        result = Parser.construct_configure(config_dict)

        assert result.ivm_config.level == transactions_pb2.MAINTENANCE_LEVEL_ALL


class TestExportCSVConfig:
    """Tests for export_csv_config function."""

    def test_export_csv_config_basic(self):
        """Test export_csv_config creates ExportCSVConfig message."""
        path = "output.csv"
        output_relation_ids = []
        config_dict = [
            ("syntax_delim", logic_pb2.Value(string_value=";")),
            ("compression", logic_pb2.Value(string_value="gzip")),
        ]

        result = Parser.export_csv_config(path, output_relation_ids, config_dict)

        assert isinstance(result, transactions_pb2.ExportCSVConfig)
        assert result.path == "output.csv"
        assert result.syntax_delim == ";"
        assert result.compression == "gzip"
        # Unspecified values use defaults
        assert result.syntax_header_row is True
        assert result.syntax_quotechar == "\""

    def test_export_csv_config_with_defaults(self):
        """Test export_csv_config with empty config uses defaults."""
        result = Parser.export_csv_config("test.csv", [], [])

        assert result.path == "test.csv"
        assert result.syntax_header_row is True
        assert result.syntax_delim == ","
        assert result.compression == ""
