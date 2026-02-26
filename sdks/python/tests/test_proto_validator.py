import os
import re

import pytest

from lqp.gen.parser import parse
from lqp.proto_validator import ValidationError, validate_proto

from .utils import (
    VALIDATOR_DIR,
    extract_expected_error,
    get_lqp_input_files,
    strip_source_location,
)


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_validate_proto_lqp_inputs(input_file):
    with open(input_file) as f:
        content = f.read()
    txn_proto, provenance = parse(content)
    validate_proto(txn_proto, provenance=provenance)


@pytest.mark.parametrize(
    "validator_file",
    sorted(f for f in os.listdir(VALIDATOR_DIR) if f.startswith("valid_")),
)
def test_valid_proto_validator_files(validator_file):
    file_path = VALIDATOR_DIR / validator_file
    with open(file_path) as f:
        content = f.read()
    txn_proto, provenance = parse(content)
    validate_proto(txn_proto, provenance=provenance, filename=validator_file)


@pytest.mark.parametrize(
    "validator_file",
    sorted(f for f in os.listdir(VALIDATOR_DIR) if f.startswith("fail_")),
)
def test_proto_validator_failure_files(validator_file):
    file_path = VALIDATOR_DIR / validator_file
    expected_error = extract_expected_error(file_path)
    if not expected_error:
        pytest.skip(f"No expected error comment found in {validator_file}")
        return
    with open(file_path) as f:
        content = f.read()
    txn_proto, provenance = parse(content)
    with pytest.raises(ValidationError) as exc_info:
        validate_proto(txn_proto, provenance=provenance, filename=validator_file)
    error_message = str(exc_info.value)
    stripped_expected = strip_source_location(expected_error)
    stripped_actual = strip_source_location(error_message)
    assert stripped_expected in stripped_actual, (
        f"Expected '{stripped_expected}' in error message: '{error_message}'"
    )


@pytest.mark.parametrize(
    "validator_file",
    sorted(f for f in os.listdir(VALIDATOR_DIR) if f.startswith("fail_")),
)
def test_proto_validator_error_has_location(validator_file):
    """Verify that errors include source location when provenance is provided."""
    file_path = VALIDATOR_DIR / validator_file
    expected_error = extract_expected_error(file_path)
    if not expected_error:
        pytest.skip(f"No expected error comment found in {validator_file}")
        return
    # Skip files whose expected error doesn't include a location.
    if not re.search(r"at\s+\S+:\d+:\d+", expected_error):
        pytest.skip(f"Expected error has no location: {validator_file}")
        return
    with open(file_path) as f:
        content = f.read()
    txn_proto, provenance = parse(content)
    with pytest.raises(ValidationError) as exc_info:
        validate_proto(txn_proto, provenance=provenance, filename=validator_file)
    error_message = str(exc_info.value)
    assert re.search(r"at\s+\S+:\d+:\d+", error_message), (
        f"Error message missing location: '{error_message}'"
    )
