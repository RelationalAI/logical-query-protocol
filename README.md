# Logical Query Protocol

[[Design document](https://docs.google.com/document/d/1QXRU7zc1SUvYkyMCG0KZINZtFgzWsl9-XHxMssdXZzg)]

## Usage

This package contains the ProtoBuf specification for the Logical Query Protocol (LQP) along
with some associated Python utilities and a human-readable language mapping to LQP. The main
user-facing functionality is the `lqp` command line tool which parses the human-readable
language.

### From PyPi
The `lqp` package is available on PyPi through `pip`. Use
```bash
pip install lqp
```

### Examples and Developer Build

See [python-tools/README.md](python-tools/README.md)

## Validate

We use the [buf utility](https://buf.build/docs/cli/quickstart/) to [validate and
lint](https://buf.build/docs/cli/quickstart/#lint-your-api) the protobuf specification. Just
follow the linked instructions and then run

```
buf lint
```

To ensure the specifications remain backward and forward compatible, you’ll want to check
for breaking changes. Protobuf itself enforces some rules (e.g., don’t reuse field numbers),
but `buf` takes this further with its [breaking change
detection](https://buf.build/docs/cli/quickstart/#detect-breaking-changes).

```
buf breaking --against ".git#subdir=proto"
```

## Developer Guide

To add a new feature to the LQP protocol, the following changes need to be made.

1. The new feature needs to be added to the protobuf specification, which is located in to `proto/` directory.
2. The Python protobuf bindings need to be build (see instructions below).
3. The new feature needs to be added to the Python IR, located in `python-tools/src/lqp/ir.py`. The structure of the IR should reflect the structure of the protobuf specification.
4. The new feature needs to be added to the grammar for the human-readable S-expression LQP syntax. The grammar is located in `python-tools/src/lqp/parser.py`.
5. The parser needs to be extended to support the new feature when translating the parse tree to the Python IR. The parsing code is located in `python-tools/src/lqp/parser.py` as well.
6. The pretty printer for the Python IR needs to be extended to support the new feature. It is located in `python-tools/src/lqp/print.py`.
7. The emitter that translates the Python IR to protobuf needs to be extended to support the new feature. It is located in `python-tools/src/lqp/emit.py`.
8. Finally, the `LQPDriver` in the `raicode` repository needs to be extended to support the new feature. To generate the Julia protobuf bindings for `raicode`, follow the instructions below.


### Building ProtoBuf Bindings

The build is [configured in `buf.gen.yaml`](https://buf.build/docs/generate/overview/), and
managed by the `build` script, which runs validation and generates Python proto code in the
`python-tools` directory.

```
./build
```

The build script depends on `protoc`. If necessary, that can be installed for example via `brew`:

```
brew install protobuf
```

If you generate new Protobuf bindings, you should also update `parser.py`, `ir.py`, `print.py`, and `emit.py`
in `python-tools/src/lqp` to reflect the changes made in the Protobuf. See the README in `python-tools/` for more details.

### Generating Julia code

Julia codegen is not supported out of the box. We get it via ProtoBuf.jl. To generate the
code, switch into the `proto/` directory and start a Julia REPL. Then do the following:

```julia
julia> using ProtoBuf

julia> protojl(readdir("relationalai/lqp/v1/", join=true), ".", "../gen/julia/", add_kwarg_constructors=true)
```

To copy the generated Julia bindings to the right place in `raicode`, run this:
```bash
cp -r logical-query-protocol/gen/julia/relationalai/ raicode/packages/LogicalQueryProtocol/src/gen/relationalai/
```

## Deployment (for Maintainers)

This package is [deployed to PyPI](https://pypi.org/project/lqp/). For maintainers, these
are the steps to deploy a new version:

1. `cd` into python-tools in the LQP repo
2. Make sure the `dist` directory is empty if it exists
3. `python -m build`
4. `python -m twine upload dist/*`
   * You will need to enter your API token for PyPi
