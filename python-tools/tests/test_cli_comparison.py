import json
import sys
import io
import subprocess
import pytest
from pathlib import Path
from .utils import get_lqp_input_files


def run_cli_with_parser(input_file, use_generated):
    """Run lqp CLI with specified parser and return JSON output."""
    old_stdout = sys.stdout

    try:
        argv = [
            input_file,
            "--json",
            "--out",
            "--generated" if use_generated else "--lark"
        ]
        if use_generated:
            argv.append("--no-validation")

        sys.stdout = io.StringIO()

        from lqp.cli import main
        old_argv = sys.argv
        sys.argv = ["lqp"] + argv
        try:
            main()
        finally:
            sys.argv = old_argv

        json_output = sys.stdout.getvalue()
        return json.loads(json_output)
    finally:
        sys.stdout = old_stdout


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_cli_parser_comparison(input_file):
    """Compare JSON output from Lark and generated parsers via CLI."""
    try:
        lark_output = run_cli_with_parser(input_file, use_generated=False)
        generated_output = run_cli_with_parser(input_file, use_generated=True)

        assert lark_output == generated_output, (
            f"Parser outputs differ for {input_file}\n"
            f"Lark: {json.dumps(lark_output, indent=2)}\n"
            f"Generated: {json.dumps(generated_output, indent=2)}"
        )

    except json.JSONDecodeError as e:
        pytest.fail(
            f"Failed to parse JSON output for {input_file}: {str(e)}"
        )
    except Exception as e:
        import traceback
        pytest.fail(
            f"Unexpected error testing {input_file}: {str(e)}\n{traceback.format_exc()}"
        )
