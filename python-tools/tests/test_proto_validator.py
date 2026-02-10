import os
import re
import pytest
from pathlib import Path

from lqp.generated_parser import parse
from lqp.parser import parse_lqp
from lqp.validator import ValidationError, validate_lqp
from lqp.proto_validator import validate_proto
import lqp.ir as ir

VALIDATOR_DIR = Path(__file__).parent / "validator"


def strip_source_location(error_str: str) -> str:
    """Remove 'at <file>:<line>:<col>' from an error string."""
    return re.sub(r'\s+at\s+\S+:\d+:\d+', '', error_str)


def extract_expected_error(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    error_match = re.search(r';;\s*ERROR:\s*(.+)(?:\n|\r\n?)', content)
    if error_match:
        return error_match.group(1).strip()
    return None


@pytest.mark.parametrize(
    "validator_file",
    [f for f in os.listdir(VALIDATOR_DIR) if f.startswith("valid_")],
)
def test_valid_proto_validator_files(validator_file):
    file_path = VALIDATOR_DIR / validator_file
    with open(file_path, "r") as f:
        content = f.read()
    txn_proto = parse(content)
    validate_proto(txn_proto)


@pytest.mark.parametrize(
    "validator_file",
    [f for f in os.listdir(VALIDATOR_DIR) if f.startswith("fail_")],
)
def test_proto_validator_failure_files(validator_file):
    file_path = VALIDATOR_DIR / validator_file
    expected_error = extract_expected_error(file_path)
    if not expected_error:
        pytest.skip(f"No expected error comment found in {validator_file}")
        return
    with open(file_path, "r") as f:
        content = f.read()
    txn_proto = parse(content)
    with pytest.raises(ValidationError) as exc_info:
        validate_proto(txn_proto)
    error_message = str(exc_info.value)
    stripped_expected = strip_source_location(expected_error)
    assert stripped_expected in error_message, (
        f"Expected '{stripped_expected}' in error message: '{error_message}'"
    )


@pytest.mark.parametrize(
    "validator_file",
    [f for f in os.listdir(VALIDATOR_DIR) if f.startswith("fail_")],
)
def test_proto_validator_matches_ir_validator(validator_file):
    """Both validators should raise ValidationError with matching messages."""
    file_path = VALIDATOR_DIR / validator_file
    expected_error = extract_expected_error(file_path)
    if not expected_error:
        pytest.skip(f"No expected error comment found in {validator_file}")
        return
    with open(file_path, "r") as f:
        content = f.read()

    # IR validator
    ir_result = parse_lqp(str(file_path), content)
    assert isinstance(ir_result, ir.Transaction)
    with pytest.raises(ValidationError) as ir_exc:
        validate_lqp(ir_result)

    # Proto validator
    txn_proto = parse(content)
    with pytest.raises(ValidationError) as proto_exc:
        validate_proto(txn_proto)

    # Compare error messages (ignoring source locations)
    ir_msg = strip_source_location(str(ir_exc.value))
    proto_msg = strip_source_location(str(proto_exc.value))
    assert ir_msg == proto_msg, (
        f"Validator messages differ:\n  IR:    {ir_msg}\n  Proto: {proto_msg}"
    )
