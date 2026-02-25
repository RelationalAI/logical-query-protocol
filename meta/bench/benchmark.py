"""
Benchmark LQP parsing and pretty-printing.

Auto-detects whether the old (Lark-based, lqp<=0.2.3) or new (generated LL(k),
lqp>=0.3.0) implementation is installed, and benchmarks accordingly.

Outputs JSON results to stdout.
"""

import json
import os
import sys
import timeit
from pathlib import Path

WARMUP_ITERATIONS = 3


def detect_version():
    """Detect which lqp version is installed based on available modules."""
    try:
        from lqp.gen.parser import parse  # noqa: F401
        return "new"
    except ImportError:
        pass
    try:
        from lqp.parser import parse_lqp  # noqa: F401
        return "old"
    except ImportError:
        pass
    print("error: no lqp package found", file=sys.stderr)
    sys.exit(1)


def find_lqp_files(tests_dir: Path):
    """Find all .lqp test files."""
    lqp_dir = tests_dir / "lqp"
    if not lqp_dir.is_dir():
        print(f"error: {lqp_dir} not found", file=sys.stderr)
        sys.exit(1)
    return sorted(lqp_dir.glob("*.lqp"))


def warmup(fn):
    """Run a function several times to warm up caches."""
    for _ in range(WARMUP_ITERATIONS):
        fn()


def bench_old(lqp_files, iterations):
    """Benchmark the old Lark-based parser and pretty-printer."""
    from lqp.emit import ir_to_proto
    from lqp.parser import parse_lqp
    from lqp.print import to_string

    results = []
    for path in lqp_files:
        name = path.stem
        text = path.read_text()
        filename = str(path)

        try:
            ir_node = parse_lqp(filename, text)
            _ = ir_to_proto(ir_node)
        except Exception:
            print(f"skip {name} (parse failed)", file=sys.stderr)
            results.append({"file": name, "parse_ms": None, "parse_emit_ms": None, "pretty_ms": None})
            continue

        def do_parse():
            return parse_lqp(filename, text)

        def do_parse_emit():
            return ir_to_proto(parse_lqp(filename, text))

        def do_pretty():
            return to_string(ir_node)

        warmup(do_parse_emit)
        parse_time = timeit.timeit(do_parse, number=iterations)
        parse_emit_time = timeit.timeit(do_parse_emit, number=iterations)

        warmup(do_pretty)
        pretty_time = timeit.timeit(do_pretty, number=iterations)

        results.append({
            "file": name,
            "parse_ms": parse_time / iterations * 1000,
            "parse_emit_ms": parse_emit_time / iterations * 1000,
            "pretty_ms": pretty_time / iterations * 1000,
        })

    return results


def bench_new(lqp_files, iterations):
    """Benchmark the new generated parser and pretty-printer."""
    from lqp.gen.parser import parse
    from lqp.gen.pretty import pretty

    results = []
    for path in lqp_files:
        name = path.stem
        text = path.read_text()

        try:
            proto = parse(text)
        except Exception:
            print(f"skip {name} (parse failed)", file=sys.stderr)
            results.append({"file": name, "parse_ms": None, "pretty_ms": None})
            continue

        def do_parse():
            return parse(text)

        def do_pretty():
            return pretty(proto)

        warmup(do_parse)
        parse_time = timeit.timeit(do_parse, number=iterations)

        warmup(do_pretty)
        pretty_time = timeit.timeit(do_pretty, number=iterations)

        results.append({
            "file": name,
            "parse_ms": parse_time / iterations * 1000,
            "pretty_ms": pretty_time / iterations * 1000,
        })

    return results


def main():
    iterations = int(os.environ.get("BENCH_ITERATIONS", "20"))
    default_tests_dir = Path(__file__).resolve().parent.parent.parent / "tests"
    tests_dir_env = os.environ.get("BENCH_TESTS_DIR")
    tests_dir = Path(tests_dir_env) if tests_dir_env else default_tests_dir

    version = detect_version()
    lqp_files = find_lqp_files(tests_dir)

    if version == "old":
        results = bench_old(lqp_files, iterations)
    else:
        results = bench_new(lqp_files, iterations)

    output = {
        "version": version,
        "iterations": iterations,
        "files": len(lqp_files),
        "results": results,
    }
    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
