# python-tools

A command-line tool to parse Logical Query Protocol (LQP) S-expressions into Protobuf binary
and JSON formats.

## Usage

```
usage: lqp [-h] [--no-validation] [--format {bin,json}] [-o OUT] input

Parse LQP S-expression into Protobuf binary and JSON files.

positional arguments:
  input                directory holding .lqp files, or a single .lqp file

options:
  -h, --help           show this help message and exit
  --no-validation      don't validate parsed LQP
  --format {bin,json}  output format (default: bin)
  -o OUT, --out OUT    output file (use '-' for stdout, default: input basename + extension specified via --format)
```

## Examples

```bash
lqp foo/bar.lqp
```
Default behavior: parse `bar.lqp` and create `bar.bin` in the same directory (binary format is default).

```bash
lqp --no-validation --format bin foo/bar.lqp
```
Will parse `bar.lqp`, compile it, and create a file `bar.bin` in the `foo/` directory.
In this case, the parser will not go through the client-side validations we do to check for well-formed LQP.

```bash
lqp --format json foo/bar.lqp
```
Parse `bar.lqp` and create `bar.json` in the `foo/` directory.

```bash
lqp --format json foo
```
This will look for `.lqp` files both at the top-level and inside an `lqp` subdirectory.
Then it will organize the generated files into their respective directories. So, for example, if `foo` has this structure:

```
foo/
| bar.lqp
| lqp/
| | baz.lqp
```
Then after executing the above command, it should have this structure:

```
foo/
| json/
| | bar.json
| | baz.json
| lqp/
| | bar.lqp
| | baz.lqp
```

```bash
lqp --format bin -o - foo.lqp
```
Write binary output to stdout. Can be piped to a file of choice: `lqp --format bin -o - foo.lqp > output.bin`.

```bash
lqp --format bin -o custom-file.bin foo.lqp
```
Write binary output to `custom-file.bin`

## Setup
It is recommended to use a Python `virtualenv`. Set one up in the `python-tools` directory
by:
```bash
cd python-tools
python -m venv .venv
```

Then activate the virtual environment:
```bash
source .venv/bin/activate
```

## Build

Install preprequisites:
```bash
pip install pip build setuptools wheel
```

Then build the module itself:
```bash
python -m build
```

Install locally:
```bash
pip install [--user] [--force-reinstall] dist/lqp-0.1.0-py3-none-any.whl
```

## Running tests

Within `python-tools`,

Setup:
```bash
python -m pip install -e ".[test]"
python -m pip install pyrefly
```

Running tests:
```bash
python -m pytest
```

To add testcases, add a `.lqp` file to the `tests/test_files/lqp_input` subdirectory. New
files get picked up automatically. To generate or update the corresponding output files
(binary, debug mode, and pretty-printing snapshots), run pytest with the
`--snapshot-update` flag.

Type checking:
```bash
pyrefly check
```

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
