@testsetup module PrettySetup

using LogicalQueryProtocol: LogicalQueryProtocol, Proto

# Module reference for method extensions in custom formatter tests.
const Pretty = LogicalQueryProtocol.Pretty

using LogicalQueryProtocol.Pretty:
    PrettyPrinter, ConstantFormatter, DefaultConstantFormatter,
    DEFAULT_CONSTANT_FORMATTER,
    format_decimal, format_int128, format_uint128,
    format_int, format_float, format_string, format_bool,
    format_string_value, format_float64,
    _pprint_dispatch, get_output, pprint, pretty, pretty_debug,
    indent!, dedent!, indent_sexp!, indent_level, try_flat

export Proto, Pretty,
    PrettyPrinter, ConstantFormatter, DefaultConstantFormatter,
    DEFAULT_CONSTANT_FORMATTER,
    format_decimal, format_int128, format_uint128,
    format_int, format_float, format_string, format_bool,
    format_string_value, format_float64,
    _pprint_dispatch, get_output, pprint, pretty, pretty_debug,
    indent!, dedent!, indent_sexp!, indent_level, try_flat

end
