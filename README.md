# Logical Query Protocol

[[Design document](https://docs.google.com/document/d/1QXRU7zc1SUvYkyMCG0KZINZtFgzWsl9-XHxMssdXZzg)]

This repository contains the ProtoBuf specification for the Logical Query Protocol (LQP),
along with SDKs for the three first-class supported languages: Python, Go, and Julia.

The SDK for each language contains the generated ProtoBuf code, along with a native parser
and pretty-printer for a human-readable representation of LQP based on S-expressions.

## Developer Guide

### Prerequisites

In order to work on the protocol, you need the following:

- the `protoc` compiler (can be installed via `brew install protobuf`)
- [buf](https://buf.build/docs/cli/quickstart/): used for validating and linting the
  protobuf specification.
- Python
- Julia
- Go

### Making changes to the protocol

Every change to the protocol should start with updating the ProtoBuf itself, which is
located in the `proto/` directory.

Remember that the protocol is in use by clients and engines that can not be updated in
lockstep, so compatibility in both directions is key. The vast majority of protocol changes
should be extensions. Existing messages can only be changed or removed when we can guarantee
that they are no longer in use by existing clients in the wild. 

In order to validate your changes and check for compatibility issues such as accidental
reuse of field numbers, run

```
make protobuf-lint
```

Please refer to the [buf
documentation](https://buf.build/docs/cli/quickstart/#detect-breaking-changes) to understand
any warnings that this check may produce.

To regenerate the ProtoBuf code for each of the three first-class languages, run

```
make protobuf
```

Check in your changes and then move on to updating the SDKs.

### Adding tests

Protocol extensions should be covered by tests, which are all located in `test/`. Just add
new `.lqp` files that make use of the new construct you are introducing. To run the tests:

```
make test
```

### Updating the SDKs

Changes to the ProtoBuf specification need to be reflected in the language-independent
grammar in `meta/grammar.y`. From the grammar we can automatically derive parsers and pretty
printers for the S-expression representation of LQP, which is used for testing and
debugging.

When you have updated the grammar, you can regenerate the parsers and verify that they match
by running

```
make parsers
make test
```

The code generators are implemented in `meta/`.

### Release (for Maintainers)

Releasing a new version of the LQP is done by releasing new versions of each of the SDKs.

This package is [deployed to PyPI](https://pypi.org/project/lqp/). For maintainers, these
are the steps to deploy a new version:

1. `cd` into python-tools in the LQP repo
2. Make sure the `dist` directory is empty if it exists
3. `python -m build`
4. `python -m twine upload dist/*`
   * You will need to enter your API token for PyPi
