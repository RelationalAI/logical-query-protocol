This repository contains the specification of the "Logical Query Protocol" (LQP for short),
along with tooling for several languages (Python, Go, and Julia) that we consider "first
class".

The protobuf specification is located in the `proto/` sub-directory. Auto-generated code by
the protobuf compiler should be in `gen/`.

Python tooling is in `python-tools/`. Check the `python-tools/README.md` for more
instructions, e.g. how to verify your changes.

For each of the three first class languages, we intend to provide the following tools:

1. A parser for the S-expression based human-readable representation of LQP.
2. A pretty printer, to convert from proto messages to the human-readable representation.
3. An IR.

Any changes to the protobuf specification will need to be reflected in all three of those.

Once the parser is updated, the test cases in `python-tools/tests/test_files/lqp` may need
to be updated accordingly.