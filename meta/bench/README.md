# LQP Parser & Pretty-Printer Benchmarks

Microbenchmarks comparing the current generated LL(k) parser and pretty-printer
(`lqp>=0.3.0`) against the old Lark-based implementation (`lqp==0.2.3`).

## What's measured

- **Parse**: full text-to-protobuf pipeline. The old version goes through an
  intermediate IR (`text → IR → protobuf`); the new version parses directly
  (`text → protobuf`).
- **Pretty-print**: protobuf/IR to text. The old version prints from its IR;
  the new version prints from protobuf messages.

All `.lqp` files under `tests/lqp/` are used as inputs. Files that fail to
parse under either version are skipped (the old parser doesn't support some
newer syntax).

## Running

```
uv run --no-project python meta/bench/run.py [iterations]
```

`iterations` defaults to 20. Each file is parsed and pretty-printed that many
times; the reported time is the per-iteration average.

The runner uses `uv run --with` to create ephemeral environments for each
version — no manual venv setup needed.

## Running a single version

To benchmark only one version (outputs JSON):

```
# Old (Lark-based)
uv run --no-project --with "lqp==0.2.3" python meta/bench/benchmark.py

# New (generated)
uv run --no-project --with ./sdks/python python meta/bench/benchmark.py
```

Control iterations via `BENCH_ITERATIONS` env var.

## Files

- `run.py` — orchestrator: runs both versions, prints comparison table.
- `benchmark.py` — timing logic: auto-detects which `lqp` is installed,
  benchmarks all test files, outputs JSON to stdout.
