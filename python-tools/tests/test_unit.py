import pytest

from lqp import ir, emit
from lqp import print as lqp_print
from lqp.proto.v1 import logic_pb2

from decimal import Decimal

def test_print_decimal_value():
    d = ir.DecimalValue(precision=18, scale=6, value=Decimal("123456789.123456"), meta=None)
    s = lqp_print.to_str(d, 0)
    assert s == "123456789.123456d18"

    d = ir.DecimalValue(precision=10, scale=2, value=Decimal("0.000123456"), meta=None)
    s = lqp_print.to_str(d, 0)
    assert s == "0.00d10"

    d = ir.DecimalValue(precision=18, scale=6, value=Decimal("0.000123456"), meta=None)
    s = lqp_print.to_str(d, 0)
    assert s == "0.000123d18"

    d = ir.DecimalValue(precision=18, scale=6, value=Decimal("123"), meta=None)
    s = lqp_print.to_str(d, 0)
    assert s == "123.000000d18"

    d = ir.DecimalValue(precision=18, scale=6, value=Decimal(4.4), meta=None)
    s = lqp_print.to_str(d, 0)
    assert s == "4.400000d18"

def test_convert_decimal_value():
    d = ir.DecimalValue(precision=18, scale=6, value=Decimal("123456789.123456"), meta=None)
    v = ir.Value(value=d, meta=None)
    converted = emit.convert_value(v)
    assert converted == logic_pb2.Value(decimal_value=logic_pb2.DecimalValue(
        precision=18,
        scale=6,
        value=logic_pb2.Int128Value(low=123456789123456, high=0)
    ))

    # -4.5 is represented by the digits 4, 5 and a sign of 1
    d = ir.DecimalValue(precision=10, scale=2, value=Decimal(-4.5), meta=None)
    v = ir.Value(value=d, meta=None)
    converted = emit.convert_value(v)
    assert converted == logic_pb2.Value(decimal_value=logic_pb2.DecimalValue(
        precision=10,
        scale=2,
        value=logic_pb2.Int128Value(low=18446744073709551166, high=18446744073709551615)
    ))

    # 4.5 is represented by the digits 4, 5
    d = ir.DecimalValue(precision=10, scale=2, value=Decimal(4.5), meta=None)
    v = ir.Value(value=d, meta=None)
    converted = emit.convert_value(v)
    assert converted == logic_pb2.Value(decimal_value=logic_pb2.DecimalValue(
        precision=10,
        scale=2,
        value=logic_pb2.Int128Value(low=450, high=0)
    ))

    # 4.4 is represented by the digits 4, 4, 0, 0, [43 others], 2, 5
    d = ir.DecimalValue(precision=10, scale=2, value=Decimal(4.4), meta=None)
    v = ir.Value(value=d, meta=None)
    converted = emit.convert_value(v)
    assert converted == logic_pb2.Value(decimal_value=logic_pb2.DecimalValue(
        precision=10,
        scale=2,
        value=logic_pb2.Int128Value(low=440, high=0)
    ))
