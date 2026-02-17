# LQP Python SDK

Python SDK for the [Logical Query Protocol](../../README.md) (LQP). Provides ProtoBuf
bindings, a parser and pretty-printer for the human-readable S-expression syntax, and a
CLI for converting between S-expression and ProtoBuf formats.

## Installation

The `lqp` package is available on [PyPI](https://pypi.org/project/lqp/). Install it with
```bash
uv add lqp
```
or, equivalently, `pip install lqp`.

## CLI Usage

To run the CLI without installing it into your project, use `uvx`:
```bash
uvx lqp --help
```

```
usage: lqp [-h] [-v] [--no-validation] [--out] [--bin | --json | --lqp] input

Parse, validate, and translate LQP files.

positional arguments:
  input            .lqp or .bin file, or a directory

options:
  -h, --help       show this help message and exit
  -v, --version    show program's version number and exit
  --no-validation  skip validation
  --out            write output to stdout
  --bin            write protobuf binary output
  --json           write protobuf JSON output
  --lqp            pretty-print LQP output
```

## Examples

```bash
lqp --no-validation --bin --json foo/bar.lqp
```
Will create two files in `foo/` named `bar.bin` and `bar.json` containing the binary and JSON encodings of the parsed ProtoBuf.
In this case, the parser will not go through the client-side validations we do to check for well-formed LQP.

```bash
lqp --bin --json foo
```
This will look for `.lqp` files both at the top-level and inside an `lqp` subdirectory.
Then it will organize the generated binary and JSON into folders, as well as the original found files. So, for example, if `foo` has this structure:

```
foo/
| bar.lqp
| lqp/
| | baz.lqp
```
Then after executing the above command, it should have this structure:

```
foo/
| bin/
| | bar.bin
| | baz.bin
| json/
| | bar.json
| | baz.json
| lqp/
| | bar.lqp
| | baz.lqp
```

```bash
lqp --bin --out foo.lqp
```
Will write the ProtoBuf binary parsed from the `foo.lqp` to stdout. The result can be piped
into the desired output file, e.g., `lqp --bin --out foo.lqp > foo.bin`.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. A `uv.lock`
file is committed to the repo to ensure reproducible builds. There is no manual setup
required — `uv run` automatically creates a virtualenv and installs locked dependencies on
first use.

From the repo root, common tasks are available via `make`:
```bash
make test-python                     # run tests (includes lint + type check)
make test-python-update-snapshots    # update test snapshots
make check-python                    # lint + type check only
make format-python                   # auto-format with ruff
```

Or run tools directly from within `sdks/python/`:
```bash
uv run lqp --help                         # run the lqp CLI from source
uv run python -m pytest                   # run tests
uv run python -m pytest --snapshot-update # update snapshots
uv run ruff check                         # lint
uv run ruff format                        # auto-format
uv run pyrefly check                      # type check
uv run python -m build                    # build distribution
```

To add testcases, add a `.lqp` file to the top-level `tests/lqp` directory. New
files get picked up automatically. To generate or update the corresponding output files
(binary, debug mode, and pretty-printing snapshots), run `pytest --snapshot-update`.

## Formatting

The LQP S-expression syntax was chosen to align with that of [the Clojure programming
language](https://clojure.org/), in order to leverage the existing tools in that ecosystem.
LQP syntax should be formatted via [cljfmt](https://github.com/weavejester/cljfmt) with the
following configuration:

```clojure
;; .cljfmt.edn
{:indents {#re ".*" [[:inner 0]]}
 :remove-surrounding-whitespace?  false
 :remove-trailing-whitespace?     false
 :remove-consecutive-blank-lines? false}
```

This configuration is explained [here](https://tonsky.me/blog/clojurefmt/) and simply works
better for LQP, which does not have many of the Clojure keywords that are treated as special
cases during formatting by default.

See the next section for an easy way to integrate `cljfmt` into your VSCode workflow.

## VSCode

Editing nested S-expressions by hand can get a little tedious, which is why
[paredit](https://calva.io/paredit/) is an established tool in the Clojure world. To
integrate `paredit` and `cljfmt` into your VSCode workflow, just install [the Calva
extension](https://calva.io/) and [follow the configuration
guide](https://calva.io/formatting/#configuration) to use the `cljfmt` configuration pasted
in the previous section.

Out-of-the-box, Calva also runs a Clojure linter, which of course does not know what to do
with LQP, resulting in lots of squiggly lines. For that reason, it is also advisable to
create the following config file at `.lsp/config.edn` from the project root:

```clojure
;; .lsp/config.edn
{:linters {:clj-kondo {:level :off}}}
```
