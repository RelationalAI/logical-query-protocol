# Logical Query Protocol

[[Design document](https://docs.google.com/document/d/1QXRU7zc1SUvYkyMCG0KZINZtFgzWsl9-XHxMssdXZzg)]

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

## Build

The build is [configured in `buf.gen.yaml`](https://buf.build/docs/generate/overview/), and
managed by the `build` script, which runs validation and generates Python proto code in the
`python-tools` directory.

```
./build
```

### Generating Julia code

Julia codegen is not supported out of the box. We get it via ProtoBuf.jl. To generate the
code, switch into the `proto/` directory and start a Julia REPL. Then do the following:

```julia
julia> using ProtoBuf

julia> protojl(readdir("relationalai/lqp/v1/", join=true), ".", "../gen/julia/", add_kwarg_constructors=true)
```

## Deployment (for Maintainers)

This package is [deployed to PyPI](https://pypi.org/project/lqp/). For maintainers, these
are the steps to deploy a new version:

1. `cd` into python-tools in the LQP repo
2. Make sure the `dist` directory is empty if it exists
3. `python -m build`
4. `python -m twine upload dist/*`
   * You will need to enter your API token for PyPi
