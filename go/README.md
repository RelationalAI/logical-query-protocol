# lqp Go package

## Navigating

The file structure mirrors that of `python-tools`:

* In `src/`:
    * `lexer.go` contains a lexer from LQP code to tokens.
    * `parser.go` contains a parser for said tokens into the LQP AST.
    * `ir.go` contains the LQP AST.
    * `emit.go` contains the compiler from LQP AST to ProtoBuf LQP.
    * `print.go` contains the pretty printing utilities for Go-native LQP AST.
* In `test/`:
    * `pretty/` contains snapshotted pretty printer test cases.
    * `parser_test.gp` contains three tests:
        * `TestParseAllLQPFiles` tests that we can parse all LQP files given in `python-tools/tests/test_files/lqp`.
        * `TestRoundTrip` tests that we can round trip: that is, pretty printed LQP can still be parsed. This is also where snapshot generation happens.
        * `TestGoPythonPrettyParity` tests that the Python and Go pretty printers are at parity.
