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
