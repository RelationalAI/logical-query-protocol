This repository contains the specification of the "Logical Query Protocol" (LQP for short),
along with tooling for several languages (Python, Go, and Julia) that we consider "first
class".

The protobuf specification is located in the `proto/` sub-directory. Auto-generated code by
the protobuf compiler shoudl be in `gen/`.

Python tooling is in `python-tools/`.

For each of the three first class languages, we intend to provide the following tools:

1. A parser for the S-expression based human-readable representation of LQP.
2. A pretty printer, to convert from proto messages to the human-readable representation.
3. An IR.