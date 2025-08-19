import pytest

from lqp import ir
from lqp import print as lqp_print

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
