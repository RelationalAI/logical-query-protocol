This repository contains the specification of the "Logical Query Protocol" (LQP for short),
along with tooling for several languages (Python, Go, and Julia) that we consider "first
class".

The protobuf specification is located in the `proto/` sub-directory. Auto-generated code by
the protobuf compiler should be in `gen/`.

SDKs for each first-class language are in `sdks/`. Check the respective README's for more
instructions. Each SDK contains a parser and pretty-printer for a S-expression
representation of the LQP, which is human-readable and meant for testing and debugging.

Any changes to the protobuf specification will need to be reflected in all SDKs.

Any changes to the protobuf specification should be covered by tests in `tests/`.

Building and testing of the ProtoBuf code and SDKs is driven by the top-level `Makefile`.