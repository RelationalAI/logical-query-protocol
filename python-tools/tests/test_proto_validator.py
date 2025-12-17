import pytest
import os

from lqp import ir, parser, validator, emit
from lqp.proto_validator import validate_lqp_proto, ValidationError
from lqp.proto.v1 import transactions_pb2

def get_validator_test_files():
    validator_dir = os.path.join(os.path.dirname(__file__), 'validator')
    return [os.path.join(validator_dir, f) for f in os.listdir(validator_dir) if f.endswith('.lqp')]

@pytest.mark.parametrize("filepath", get_validator_test_files())
def test_proto_validator_parity(filepath):
    # First, run the existing IR validator
    ir_error = None
    try:
        lqp_ir = parser.parse_file(filepath)
        assert isinstance(lqp_ir, ir.Transaction), f"Expected Transaction, got {type(lqp_ir)}"
        validator.validate_lqp(lqp_ir)
    except validator.ValidationError as e:
        ir_error = e

    # Now, run the new proto validator
    proto_error = None
    try:
        # We need to get the proto bytes first, then parse them
        # Re-parsing the file to get a fresh IR object
        lqp_ir_for_emit = parser.parse_file(filepath)
        assert isinstance(lqp_ir_for_emit, ir.Transaction), f"Expected Transaction, got {type(lqp_ir_for_emit)}"
        proto_bytes = emit.emit_transaction(lqp_ir_for_emit)

        transaction_proto = transactions_pb2.Transaction()
        transaction_proto.ParseFromString(proto_bytes)

        validate_lqp_proto(transaction_proto)
    except ValidationError as e:
        proto_error = e
    except Exception as e:
        # Catching other exceptions to aid debugging
        proto_error = e


    if ir_error is None and proto_error is not None:
        pytest.fail(f"IR validator passed, but proto validator failed for {os.path.basename(filepath)} with: {proto_error}")
    if ir_error is not None and proto_error is None:
        pytest.fail(f"Proto validator passed, but IR validator failed for {os.path.basename(filepath)} with: {ir_error}")

    # If both failed, we can consider it a pass for now.
    # A more robust check would be to compare the error messages, but that's brittle.
    assert (ir_error is None) == (proto_error is None)
