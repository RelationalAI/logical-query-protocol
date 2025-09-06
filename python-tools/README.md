# python-tools

A command-line tool to parse Logical Query Protocol (LQP) S-expressions into Protobuf binary
and JSON formats.

## Usage

```
usage: lqp [-h] [--bin BIN] [--json JSON] input_directory

Parse LQP S-expression into Protobuf binary and JSON files.

positional arguments:
  input_directory  path to the input LQP S-expression files

options:
  -h, --help       show this help message and exit
  --bin BIN        output directory for the binary encoded protobuf
  --json JSON      output directory for the JSON encoded protobuf
```

## Build

Install preprequisites:
```
pip install pip build setuptools wheel
```

Then build the module itself:
```
python -m build
```

Install locally:
```
pip install [--user] [--force-reinstall] dist/lqp-0.1.0-py3-none-any.whl
```

## Running tests

Within `python-tools`,

Setup:
```
python -m pip install -e ".[test]"
python -m pip install pyrefly
```

Running tests:
```
python -m pytest
```

Type checking:
```
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
