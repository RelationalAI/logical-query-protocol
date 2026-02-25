#!/usr/bin/env python3
"""
Run LQP parser/pretty-printer benchmarks comparing old (Lark) vs new (generated).

Uses `uv run --with` to create ephemeral environments for each version.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_SCRIPT = Path(__file__).resolve().parent / "benchmark.py"
SDK_PYTHON = REPO_ROOT / "sdks" / "python"
TESTS_DIR = REPO_ROOT / "tests"
OLD_PACKAGE = "lqp==0.2.3"


def run_benchmark(label: str, with_pkg: str, iterations: int):
    """Run benchmark.py in an ephemeral uv environment."""
    env = {
        **os.environ,
        "BENCH_TESTS_DIR": str(TESTS_DIR),
        "BENCH_ITERATIONS": str(iterations),
    }
    cmd = [
        "uv",
        "run",
        "--no-project",
        "--with",
        with_pkg,
        "python",
        str(BENCHMARK_SCRIPT),
    ]
    print(f"Running {label} benchmarks...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        print(f"error: {label} benchmark failed", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def fmt_speedup(old_ms, new_ms):
    """Format a speedup ratio."""
    if new_ms > 0:
        return f"{old_ms / new_ms:>7.2f}x"
    return f"{'inf':>7}"


def print_parse_table(old_by_file, new_by_file, all_files):
    """Print parser comparison table."""
    print()
    print("## Parser")
    print()
    hdr = f"{'file':<25} {'old parse':>10} {'old p+emit':>11} {'new parse':>10} {'speedup':>8}"
    print(hdr)
    print("-" * len(hdr))

    total_old = 0.0
    total_old_emit = 0.0
    total_new = 0.0
    skipped = 0
    compared = 0

    for f in all_files:
        o = old_by_file[f]
        n = new_by_file[f]

        po = o["parse_ms"]
        peo = o.get("parse_emit_ms")
        pn = n["parse_ms"]

        if po is None or pn is None:
            print(f"{f:<25} {'skip':>10} {'skip':>11} {'skip':>10} {'':>8}")
            skipped += 1
            continue

        compared += 1
        pe = peo if peo else po
        total_old += po
        total_old_emit += pe
        total_new += pn

        print(f"{f:<25} {po:>9.3f}ms {pe:>10.3f}ms {pn:>9.3f}ms {fmt_speedup(pe, pn)}")

    print("-" * len(hdr))
    print(
        f"{'TOTAL':<25} {total_old:>9.3f}ms {total_old_emit:>10.3f}ms"
        f" {total_new:>9.3f}ms {fmt_speedup(total_old_emit, total_new)}"
    )

    print()
    print("old parse   = Lark parse to IR")
    print("old p+emit  = Lark parse to IR + ir_to_proto")
    print("new parse   = generated LL(k) parser to protobuf")
    print("speedup     = old p+emit / new parse")

    return compared, skipped


def print_pretty_table(old_by_file, new_by_file, all_files):
    """Print pretty-printer comparison table."""
    print()
    print("## Pretty-printer")
    print()
    hdr = f"{'file':<25} {'old':>10} {'new':>10} {'speedup':>8}"
    print(hdr)
    print("-" * len(hdr))

    total_old = 0.0
    total_new = 0.0

    for f in all_files:
        o = old_by_file[f]
        n = new_by_file[f]

        pro = o["pretty_ms"]
        prn = n["pretty_ms"]

        if pro is None or prn is None:
            print(f"{f:<25} {'skip':>10} {'skip':>10} {'':>8}")
            continue

        total_old += pro
        total_new += prn

        print(f"{f:<25} {pro:>9.3f}ms {prn:>9.3f}ms {fmt_speedup(pro, prn)}")

    print("-" * len(hdr))
    print(
        f"{'TOTAL':<25} {total_old:>9.3f}ms {total_new:>9.3f}ms {fmt_speedup(total_old, total_new)}"
    )

    print()
    print("old = IR to text")
    print("new = protobuf to text")


def print_comparison(old_data, new_data):
    """Print formatted comparison tables."""
    old_by_file = {r["file"]: r for r in old_data["results"]}
    new_by_file = {r["file"]: r for r in new_data["results"]}
    all_files = sorted(set(old_by_file) & set(new_by_file))

    compared, skipped = print_parse_table(old_by_file, new_by_file, all_files)
    print_pretty_table(old_by_file, new_by_file, all_files)

    print()
    print(f"Iterations per file: {old_data['iterations']}")
    print(f"Files compared: {compared}")
    if skipped:
        print(f"Files skipped: {skipped} (unsupported by old parser)")


def main():
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    old_data = run_benchmark("old (Lark)", OLD_PACKAGE, iterations)
    new_data = run_benchmark("new (generated)", str(SDK_PYTHON), iterations)
    print_comparison(old_data, new_data)


if __name__ == "__main__":
    main()
