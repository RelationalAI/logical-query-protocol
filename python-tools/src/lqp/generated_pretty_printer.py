"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer python
"""

from io import StringIO
from typing import Any, IO

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: IO[str] = None):
        self.io = io if io is not None else StringIO()
        self.indent_level = 0
        self.at_line_start = True

    def write(self, s: str) -> None:
        """Write a string to the output, with indentation at line start."""
        if self.at_line_start and s.strip():
            self.io.write('  ' * self.indent_level)
            self.at_line_start = False
        self.io.write(s)

    def newline(self) -> None:
        """Write a newline to the output."""
        self.io.write('\n')
        self.at_line_start = True

    def indent(self, delta: int = 1) -> None:
        """Increase indentation level."""
        self.indent_level += delta

    def dedent(self, delta: int = 1) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - delta)

    def get_output(self) -> str:
        """Get the accumulated output as a string."""
        if isinstance(self.io, StringIO):
            return self.io.getvalue()
        return ""

    def format_decimal(self, msg) -> str:
        """Format a DecimalValue protobuf message as a string."""
        # DecimalValue has 'value' field as string
        return str(msg.value) if msg.value else "0"

    def format_int128(self, msg) -> str:
        """Format an Int128Value protobuf message as a string."""
        value = (msg.high << 64) | msg.low
        if msg.high & (1 << 63):
            value -= (1 << 128)
        return str(value)

    def format_uint128(self, msg) -> str:
        """Format a UInt128Value protobuf message as a hex string."""
        value = (msg.high << 64) | msg.low
        return f"0x{value:032x}"

    def fragment_id_to_string(self, msg) -> str:
        """Convert FragmentId to string representation."""
        return msg.id.decode('utf-8') if msg.id else ""

    def relation_id_to_string(self, msg):
        """Convert RelationId to string representation if it has symbol."""
        if msg.symbol:
            return msg.symbol
        return None

    def relation_id_to_int(self, msg):
        """Convert RelationId to int representation if it has id."""
        if msg.id_low or msg.id_high:
            return (msg.id_high << 64) | msg.id_low
        return None

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> Optional[Never]:
        def _t493(_dollar_dollar):
            _t494 = Parser.is_default_configure(_dollar_dollar.configure)
            
            if not _t494:
                _t495 = (_dollar_dollar.configure, _dollar_dollar.sync, _dollar_dollar.epochs,)
            else:
                _t495 = None
            return _t495
        _t496 = _t493(msg)
        fields0 = _t496
        unwrapped_fields1 = fields0
        self.write('(')
        self.write('transaction')
        self.newline()
        self.indent()
        field2 = unwrapped_fields1[0]
        
        if field2 is not None:
            opt_val3 = field2
            _t498 = self.pretty_configure(opt_val3)
            _t497 = _t498
        else:
            _t497 = None
        self.newline()
        field4 = unwrapped_fields1[1]
        
        if field4 is not None:
            opt_val5 = field4
            _t500 = self.pretty_sync(opt_val5)
            _t499 = _t500
        else:
            _t499 = None
        self.newline()
        field6 = unwrapped_fields1[2]
        for i8, elem7 in enumerate(field6):
            
            if (i8 > 0):
                self.newline()
                _t501 = None
            else:
                _t501 = None
            _t502 = self.pretty_epoch(elem7)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> Optional[Never]:
        def _t503(_dollar_dollar):
            _t504 = Parser.deconstruct_configure(_dollar_dollar)
            return _t504
        _t505 = _t503(msg)
        fields9 = _t505
        unwrapped_fields10 = fields9
        self.write('(')
        self.write('configure')
        self.newline()
        self.indent()
        _t506 = self.pretty_config_dict(unwrapped_fields10)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_config_dict(self, msg: list[tuple[str, logic_pb2.Value]]) -> Optional[Never]:
        def _t507(_dollar_dollar):
            return _dollar_dollar
        _t508 = _t507(msg)
        fields11 = _t508
        unwrapped_fields12 = fields11
        self.write('{')
        for i14, elem13 in enumerate(unwrapped_fields12):
            
            if (i14 > 0):
                self.newline()
                _t509 = None
            else:
                _t509 = None
            _t510 = self.pretty_config_key_value(elem13)
        self.write('}')
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> Optional[Never]:
        def _t511(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t512 = _t511(msg)
        fields15 = _t512
        unwrapped_fields16 = fields15
        self.write(':')
        field17 = unwrapped_fields16[0]
        self.write(field17)
        field18 = unwrapped_fields16[1]
        _t513 = self.pretty_value(field18)
        return _t513

    def pretty_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t514(_dollar_dollar):
            
            if _dollar_dollar.HasField('date_value'):
                _t515 = _dollar_dollar.date_value
            else:
                _t515 = None
            return _t515
        _t516 = _t514(msg)
        deconstruct_result29 = _t516
        
        if deconstruct_result29 is not None:
            _t518 = self.pretty_date(deconstruct_result29)
            _t517 = _t518
        else:
            def _t519(_dollar_dollar):
                
                if _dollar_dollar.HasField('datetime_value'):
                    _t520 = _dollar_dollar.datetime_value
                else:
                    _t520 = None
                return _t520
            _t521 = _t519(msg)
            deconstruct_result28 = _t521
            
            if deconstruct_result28 is not None:
                _t523 = self.pretty_datetime(deconstruct_result28)
                _t522 = _t523
            else:
                def _t524(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('string_value'):
                        _t525 = _dollar_dollar.string_value
                    else:
                        _t525 = None
                    return _t525
                _t526 = _t524(msg)
                deconstruct_result27 = _t526
                
                if deconstruct_result27 is not None:
                    self.write(repr(deconstruct_result27))
                    _t527 = None
                else:
                    def _t528(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('int_value'):
                            _t529 = _dollar_dollar.int_value
                        else:
                            _t529 = None
                        return _t529
                    _t530 = _t528(msg)
                    deconstruct_result26 = _t530
                    
                    if deconstruct_result26 is not None:
                        self.write(str(deconstruct_result26))
                        _t531 = None
                    else:
                        def _t532(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('float_value'):
                                _t533 = _dollar_dollar.float_value
                            else:
                                _t533 = None
                            return _t533
                        _t534 = _t532(msg)
                        deconstruct_result25 = _t534
                        
                        if deconstruct_result25 is not None:
                            self.write(str(deconstruct_result25))
                            _t535 = None
                        else:
                            def _t536(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('uint128_value'):
                                    _t537 = _dollar_dollar.uint128_value
                                else:
                                    _t537 = None
                                return _t537
                            _t538 = _t536(msg)
                            deconstruct_result24 = _t538
                            
                            if deconstruct_result24 is not None:
                                self.write(str(deconstruct_result24))
                                _t539 = None
                            else:
                                def _t540(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('int128_value'):
                                        _t541 = _dollar_dollar.int128_value
                                    else:
                                        _t541 = None
                                    return _t541
                                _t542 = _t540(msg)
                                deconstruct_result23 = _t542
                                
                                if deconstruct_result23 is not None:
                                    self.write(str(deconstruct_result23))
                                    _t543 = None
                                else:
                                    def _t544(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('decimal_value'):
                                            _t545 = _dollar_dollar.decimal_value
                                        else:
                                            _t545 = None
                                        return _t545
                                    _t546 = _t544(msg)
                                    deconstruct_result22 = _t546
                                    
                                    if deconstruct_result22 is not None:
                                        self.write(str(deconstruct_result22))
                                        _t547 = None
                                    else:
                                        def _t548(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('boolean_value'):
                                                _t549 = _dollar_dollar.boolean_value
                                            else:
                                                _t549 = None
                                            return _t549
                                        _t550 = _t548(msg)
                                        deconstruct_result21 = _t550
                                        
                                        if deconstruct_result21 is not None:
                                            _t552 = self.pretty_boolean_value(deconstruct_result21)
                                            _t551 = _t552
                                        else:
                                            def _t553(_dollar_dollar):
                                                return _dollar_dollar
                                            _t554 = _t553(msg)
                                            fields19 = _t554
                                            unwrapped_fields20 = fields19
                                            self.write('missing')
                                            _t551 = None
                                        _t547 = _t551
                                    _t543 = _t547
                                _t539 = _t543
                            _t535 = _t539
                        _t531 = _t535
                    _t527 = _t531
                _t522 = _t527
            _t517 = _t522
        return _t517

    def pretty_date(self, msg: logic_pb2.DateValue) -> Optional[Never]:
        def _t555(_dollar_dollar):
            _t556 = self.int32_to_int64(_dollar_dollar.year)
            _t557 = self.int32_to_int64(_dollar_dollar.month)
            _t558 = self.int32_to_int64(_dollar_dollar.day)
            return (_t556, _t557, _t558,)
        _t559 = _t555(msg)
        fields30 = _t559
        unwrapped_fields31 = fields30
        self.write('(')
        self.write('date')
        self.newline()
        self.indent()
        field32 = unwrapped_fields31[0]
        self.write(str(field32))
        self.newline()
        field33 = unwrapped_fields31[1]
        self.write(str(field33))
        self.newline()
        field34 = unwrapped_fields31[2]
        self.write(str(field34))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue) -> Optional[Never]:
        def _t560(_dollar_dollar):
            _t561 = self.int32_to_int64(_dollar_dollar.year)
            _t562 = self.int32_to_int64(_dollar_dollar.month)
            _t563 = self.int32_to_int64(_dollar_dollar.day)
            _t564 = self.int32_to_int64(_dollar_dollar.hour)
            _t565 = self.int32_to_int64(_dollar_dollar.minute)
            _t566 = self.int32_to_int64(_dollar_dollar.second)
            _t567 = self.int32_to_int64(_dollar_dollar.microsecond)
            return (_t561, _t562, _t563, _t564, _t565, _t566, _t567,)
        _t568 = _t560(msg)
        fields35 = _t568
        unwrapped_fields36 = fields35
        self.write('(')
        self.write('datetime')
        self.newline()
        self.indent()
        field37 = unwrapped_fields36[0]
        self.write(str(field37))
        self.newline()
        field38 = unwrapped_fields36[1]
        self.write(str(field38))
        self.newline()
        field39 = unwrapped_fields36[2]
        self.write(str(field39))
        self.newline()
        field40 = unwrapped_fields36[3]
        self.write(str(field40))
        self.newline()
        field41 = unwrapped_fields36[4]
        self.write(str(field41))
        self.newline()
        field42 = unwrapped_fields36[5]
        self.write(str(field42))
        self.newline()
        field43 = unwrapped_fields36[6]
        
        if field43 is not None:
            opt_val44 = field43
            self.write(str(opt_val44))
            _t569 = None
        else:
            _t569 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_boolean_value(self, msg: bool) -> Optional[Never]:
        def _t570(_dollar_dollar):
            return _dollar_dollar
        _t571 = _t570(msg)
        fields47 = _t571
        unwrapped_fields48 = fields47
        self.write('true')
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> Optional[Never]:
        def _t572(_dollar_dollar):
            return _dollar_dollar.fragments
        _t573 = _t572(msg)
        fields49 = _t573
        unwrapped_fields50 = fields49
        self.write('(')
        self.write('sync')
        self.newline()
        self.indent()
        for i52, elem51 in enumerate(unwrapped_fields50):
            
            if (i52 > 0):
                self.newline()
                _t574 = None
            else:
                _t574 = None
            _t575 = self.pretty_fragment_id(elem51)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t576(_dollar_dollar):
            _t577 = self.fragment_id_to_string(_dollar_dollar)
            return _t577
        _t578 = _t576(msg)
        fields53 = _t578
        unwrapped_fields54 = fields53
        self.write(':')
        self.write(unwrapped_fields54)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> Optional[Never]:
        def _t579(_dollar_dollar):
            _t580 = self.is_empty(_dollar_dollar.writes)
            _t581 = self.is_empty(_dollar_dollar.reads)
            
            if (not _t580 and not _t581):
                _t582 = (_dollar_dollar.writes, _dollar_dollar.reads,)
            else:
                _t582 = None
            return _t582
        _t583 = _t579(msg)
        fields55 = _t583
        unwrapped_fields56 = fields55
        self.write('(')
        self.write('epoch')
        self.newline()
        self.indent()
        field57 = unwrapped_fields56[0]
        
        if field57 is not None:
            opt_val58 = field57
            _t585 = self.pretty_epoch_writes(opt_val58)
            _t584 = _t585
        else:
            _t584 = None
        self.newline()
        field59 = unwrapped_fields56[1]
        
        if field59 is not None:
            opt_val60 = field59
            _t587 = self.pretty_epoch_reads(opt_val60)
            _t586 = _t587
        else:
            _t586 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_epoch_writes(self, msg: list[transactions_pb2.Write]) -> Optional[Never]:
        def _t588(_dollar_dollar):
            return _dollar_dollar
        _t589 = _t588(msg)
        fields61 = _t589
        unwrapped_fields62 = fields61
        self.write('(')
        self.write('writes')
        self.newline()
        self.indent()
        for i64, elem63 in enumerate(unwrapped_fields62):
            
            if (i64 > 0):
                self.newline()
                _t590 = None
            else:
                _t590 = None
            _t591 = self.pretty_write(elem63)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> Optional[Never]:
        def _t592(_dollar_dollar):
            
            if _dollar_dollar.HasField('define'):
                _t593 = _dollar_dollar.define
            else:
                _t593 = None
            return _t593
        _t594 = _t592(msg)
        deconstruct_result67 = _t594
        
        if deconstruct_result67 is not None:
            _t596 = self.pretty_define(deconstruct_result67)
            _t595 = _t596
        else:
            def _t597(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t598 = _dollar_dollar.undefine
                else:
                    _t598 = None
                return _t598
            _t599 = _t597(msg)
            deconstruct_result66 = _t599
            
            if deconstruct_result66 is not None:
                _t601 = self.pretty_undefine(deconstruct_result66)
                _t600 = _t601
            else:
                def _t602(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t603 = _dollar_dollar.context
                    else:
                        _t603 = None
                    return _t603
                _t604 = _t602(msg)
                deconstruct_result65 = _t604
                
                if deconstruct_result65 is not None:
                    _t606 = self.pretty_context(deconstruct_result65)
                    _t605 = _t606
                else:
                    raise ParseError('No matching rule for write')
                _t600 = _t605
            _t595 = _t600
        return _t595

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[Never]:
        def _t607(_dollar_dollar):
            return _dollar_dollar.fragment
        _t608 = _t607(msg)
        fields68 = _t608
        unwrapped_fields69 = fields68
        self.write('(')
        self.write('define')
        self.newline()
        self.indent()
        _t609 = self.pretty_fragment(unwrapped_fields69)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[Never]:
        def _t610(_dollar_dollar):
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t611 = _t610(msg)
        fields70 = _t611
        unwrapped_fields71 = fields70
        self.write('(')
        self.write('fragment')
        self.newline()
        self.indent()
        field72 = unwrapped_fields71[0]
        _t612 = self.pretty_new_fragment_id(field72)
        self.newline()
        field73 = unwrapped_fields71[1]
        for i75, elem74 in enumerate(field73):
            
            if (i75 > 0):
                self.newline()
                _t613 = None
            else:
                _t613 = None
            _t614 = self.pretty_declaration(elem74)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t615(_dollar_dollar):
            return _dollar_dollar
        _t616 = _t615(msg)
        fields76 = _t616
        unwrapped_fields77 = fields76
        _t617 = self.pretty_fragment_id(unwrapped_fields77)
        return _t617

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[Never]:
        def _t618(_dollar_dollar):
            _t619 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t619:
                _t620 = (_dollar_dollar.name, _dollar_dollar.body, _dollar_dollar.attrs,)
            else:
                _t620 = None
            return _t620
        _t621 = _t618(msg)
        guard_result81 = _t621
        
        if guard_result81 is not None:
            _t623 = self.pretty_def(msg)
            _t622 = _t623
        else:
            def _t624(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t625 = _dollar_dollar.algorithm
                else:
                    _t625 = None
                return _t625
            _t626 = _t624(msg)
            deconstruct_result80 = _t626
            
            if deconstruct_result80 is not None:
                _t628 = self.pretty_algorithm(deconstruct_result80)
                _t627 = _t628
            else:
                def _t629(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t630 = _dollar_dollar.constraint
                    else:
                        _t630 = None
                    return _t630
                _t631 = _t629(msg)
                deconstruct_result79 = _t631
                
                if deconstruct_result79 is not None:
                    _t633 = self.pretty_constraint(deconstruct_result79)
                    _t632 = _t633
                else:
                    def _t634(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('rel_edb'):
                            _t635 = _dollar_dollar.rel_edb
                        else:
                            _t635 = None
                        return _t635
                    _t636 = _t634(msg)
                    guard_result78 = _t636
                    
                    if guard_result78 is not None:
                        _t638 = self.pretty_data(msg)
                        _t637 = _t638
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t632 = _t637
                _t627 = _t632
            _t622 = _t627
        return _t622

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[Never]:
        def _t639(_dollar_dollar):
            _t640 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t640:
                _t641 = (_dollar_dollar.name, _dollar_dollar.body, _dollar_dollar.attrs,)
            else:
                _t641 = None
            return _t641
        _t642 = _t639(msg)
        fields82 = _t642
        unwrapped_fields83 = fields82
        self.write('(')
        self.write('def')
        self.newline()
        self.indent()
        field84 = unwrapped_fields83[0]
        _t643 = self.pretty_relation_id(field84)
        self.newline()
        field85 = unwrapped_fields83[1]
        _t644 = self.pretty_abstraction(field85)
        self.newline()
        field86 = unwrapped_fields83[2]
        
        if field86 is not None:
            opt_val87 = field86
            _t646 = self.pretty_attrs(opt_val87)
            _t645 = _t646
        else:
            _t645 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[Never]:
        def _t647(_dollar_dollar):
            _t648 = Parser.deconstruct_relation_id_string(_dollar_dollar)
            return _t648
        _t649 = _t647(msg)
        deconstruct_result89 = _t649
        
        if deconstruct_result89 is not None:
            self.write(':')
            self.write(deconstruct_result89)
            _t650 = None
        else:
            def _t651(_dollar_dollar):
                _t652 = Parser.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t652
            _t653 = _t651(msg)
            deconstruct_result88 = _t653
            
            if deconstruct_result88 is not None:
                self.write(str(deconstruct_result88))
                _t654 = None
            else:
                raise ParseError('No matching rule for relation_id')
            _t650 = _t654
        return _t650

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[Never]:
        def _t655(_dollar_dollar):
            _t656 = Parser.deconstruct_bindings(_dollar_dollar)
            return (_t656, _dollar_dollar.value,)
        _t657 = _t655(msg)
        fields90 = _t657
        unwrapped_fields91 = fields90
        self.write('(')
        field92 = unwrapped_fields91[0]
        _t658 = self.pretty_bindings(field92)
        field93 = unwrapped_fields91[1]
        _t659 = self.pretty_formula(field93)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_bindings(self, msg: tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]) -> Optional[Never]:
        def _t660(_dollar_dollar):
            _t661 = self.is_empty(_dollar_dollar[1])
            
            if not _t661:
                _t662 = (_dollar_dollar[0], _dollar_dollar[1],)
            else:
                _t662 = None
            return _t662
        _t663 = _t660(msg)
        fields94 = _t663
        unwrapped_fields95 = fields94
        self.write('[')
        field96 = unwrapped_fields95[0]
        for i98, elem97 in enumerate(field96):
            
            if (i98 > 0):
                self.newline()
                _t664 = None
            else:
                _t664 = None
            _t665 = self.pretty_binding(elem97)
        field99 = unwrapped_fields95[1]
        
        if field99 is not None:
            opt_val100 = field99
            _t667 = self.pretty_value_bindings(opt_val100)
            _t666 = _t667
        else:
            _t666 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[Never]:
        def _t668(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t669 = _t668(msg)
        fields101 = _t669
        unwrapped_fields102 = fields101
        field103 = unwrapped_fields102[0]
        self.write(field103)
        self.write('::')
        field104 = unwrapped_fields102[1]
        _t670 = self.pretty_type(field104)
        return _t670

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[Never]:
        def _t671(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t672 = _dollar_dollar.unspecified_type
            else:
                _t672 = None
            return _t672
        _t673 = _t671(msg)
        deconstruct_result115 = _t673
        
        if deconstruct_result115 is not None:
            _t675 = self.pretty_unspecified_type(deconstruct_result115)
            _t674 = _t675
        else:
            def _t676(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t677 = _dollar_dollar.string_type
                else:
                    _t677 = None
                return _t677
            _t678 = _t676(msg)
            deconstruct_result114 = _t678
            
            if deconstruct_result114 is not None:
                _t680 = self.pretty_string_type(deconstruct_result114)
                _t679 = _t680
            else:
                def _t681(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t682 = _dollar_dollar.int_type
                    else:
                        _t682 = None
                    return _t682
                _t683 = _t681(msg)
                deconstruct_result113 = _t683
                
                if deconstruct_result113 is not None:
                    _t685 = self.pretty_int_type(deconstruct_result113)
                    _t684 = _t685
                else:
                    def _t686(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t687 = _dollar_dollar.float_type
                        else:
                            _t687 = None
                        return _t687
                    _t688 = _t686(msg)
                    deconstruct_result112 = _t688
                    
                    if deconstruct_result112 is not None:
                        _t690 = self.pretty_float_type(deconstruct_result112)
                        _t689 = _t690
                    else:
                        def _t691(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t692 = _dollar_dollar.uint128_type
                            else:
                                _t692 = None
                            return _t692
                        _t693 = _t691(msg)
                        deconstruct_result111 = _t693
                        
                        if deconstruct_result111 is not None:
                            _t695 = self.pretty_uint128_type(deconstruct_result111)
                            _t694 = _t695
                        else:
                            def _t696(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t697 = _dollar_dollar.int128_type
                                else:
                                    _t697 = None
                                return _t697
                            _t698 = _t696(msg)
                            deconstruct_result110 = _t698
                            
                            if deconstruct_result110 is not None:
                                _t700 = self.pretty_int128_type(deconstruct_result110)
                                _t699 = _t700
                            else:
                                def _t701(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t702 = _dollar_dollar.date_type
                                    else:
                                        _t702 = None
                                    return _t702
                                _t703 = _t701(msg)
                                deconstruct_result109 = _t703
                                
                                if deconstruct_result109 is not None:
                                    _t705 = self.pretty_date_type(deconstruct_result109)
                                    _t704 = _t705
                                else:
                                    def _t706(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t707 = _dollar_dollar.datetime_type
                                        else:
                                            _t707 = None
                                        return _t707
                                    _t708 = _t706(msg)
                                    deconstruct_result108 = _t708
                                    
                                    if deconstruct_result108 is not None:
                                        _t710 = self.pretty_datetime_type(deconstruct_result108)
                                        _t709 = _t710
                                    else:
                                        def _t711(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t712 = _dollar_dollar.missing_type
                                            else:
                                                _t712 = None
                                            return _t712
                                        _t713 = _t711(msg)
                                        deconstruct_result107 = _t713
                                        
                                        if deconstruct_result107 is not None:
                                            _t715 = self.pretty_missing_type(deconstruct_result107)
                                            _t714 = _t715
                                        else:
                                            def _t716(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t717 = _dollar_dollar.decimal_type
                                                else:
                                                    _t717 = None
                                                return _t717
                                            _t718 = _t716(msg)
                                            deconstruct_result106 = _t718
                                            
                                            if deconstruct_result106 is not None:
                                                _t720 = self.pretty_decimal_type(deconstruct_result106)
                                                _t719 = _t720
                                            else:
                                                def _t721(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t722 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t722 = None
                                                    return _t722
                                                _t723 = _t721(msg)
                                                deconstruct_result105 = _t723
                                                
                                                if deconstruct_result105 is not None:
                                                    _t725 = self.pretty_boolean_type(deconstruct_result105)
                                                    _t724 = _t725
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t719 = _t724
                                            _t714 = _t719
                                        _t709 = _t714
                                    _t704 = _t709
                                _t699 = _t704
                            _t694 = _t699
                        _t689 = _t694
                    _t684 = _t689
                _t679 = _t684
            _t674 = _t679
        return _t674

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[Never]:
        def _t726(_dollar_dollar):
            return _dollar_dollar
        _t727 = _t726(msg)
        fields116 = _t727
        unwrapped_fields117 = fields116
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[Never]:
        def _t728(_dollar_dollar):
            return _dollar_dollar
        _t729 = _t728(msg)
        fields118 = _t729
        unwrapped_fields119 = fields118
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[Never]:
        def _t730(_dollar_dollar):
            return _dollar_dollar
        _t731 = _t730(msg)
        fields120 = _t731
        unwrapped_fields121 = fields120
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[Never]:
        def _t732(_dollar_dollar):
            return _dollar_dollar
        _t733 = _t732(msg)
        fields122 = _t733
        unwrapped_fields123 = fields122
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[Never]:
        def _t734(_dollar_dollar):
            return _dollar_dollar
        _t735 = _t734(msg)
        fields124 = _t735
        unwrapped_fields125 = fields124
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[Never]:
        def _t736(_dollar_dollar):
            return _dollar_dollar
        _t737 = _t736(msg)
        fields126 = _t737
        unwrapped_fields127 = fields126
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[Never]:
        def _t738(_dollar_dollar):
            return _dollar_dollar
        _t739 = _t738(msg)
        fields128 = _t739
        unwrapped_fields129 = fields128
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[Never]:
        def _t740(_dollar_dollar):
            return _dollar_dollar
        _t741 = _t740(msg)
        fields130 = _t741
        unwrapped_fields131 = fields130
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[Never]:
        def _t742(_dollar_dollar):
            return _dollar_dollar
        _t743 = _t742(msg)
        fields132 = _t743
        unwrapped_fields133 = fields132
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[Never]:
        def _t744(_dollar_dollar):
            _t745 = self.int32_to_int64(_dollar_dollar.precision)
            _t746 = self.int32_to_int64(_dollar_dollar.scale)
            return (_t745, _t746,)
        _t747 = _t744(msg)
        fields134 = _t747
        unwrapped_fields135 = fields134
        self.write('(')
        self.write('DECIMAL')
        self.newline()
        self.indent()
        field136 = unwrapped_fields135[0]
        self.write(str(field136))
        self.newline()
        field137 = unwrapped_fields135[1]
        self.write(str(field137))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> Optional[Never]:
        def _t748(_dollar_dollar):
            return _dollar_dollar
        _t749 = _t748(msg)
        fields138 = _t749
        unwrapped_fields139 = fields138
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: list[logic_pb2.Binding]) -> Optional[Never]:
        def _t750(_dollar_dollar):
            return _dollar_dollar
        _t751 = _t750(msg)
        fields140 = _t751
        unwrapped_fields141 = fields140
        self.write('|')
        for i143, elem142 in enumerate(unwrapped_fields141):
            
            if (i143 > 0):
                self.newline()
                _t752 = None
            else:
                _t752 = None
            _t753 = self.pretty_binding(elem142)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[Never]:
        def _t754(_dollar_dollar):
            _t755 = self.is_empty(_dollar_dollar.conjunction.args)
            
            if (_dollar_dollar.HasField('conjunction') and _t755):
                _t756 = _dollar_dollar.conjunction
            else:
                _t756 = None
            return _t756
        _t757 = _t754(msg)
        deconstruct_result156 = _t757
        
        if deconstruct_result156 is not None:
            _t759 = self.pretty_true(deconstruct_result156)
            _t758 = _t759
        else:
            def _t760(_dollar_dollar):
                _t761 = self.is_empty(_dollar_dollar.disjunction.args)
                
                if (_dollar_dollar.HasField('disjunction') and _t761):
                    _t762 = _dollar_dollar.disjunction
                else:
                    _t762 = None
                return _t762
            _t763 = _t760(msg)
            deconstruct_result155 = _t763
            
            if deconstruct_result155 is not None:
                _t765 = self.pretty_false(deconstruct_result155)
                _t764 = _t765
            else:
                def _t766(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t767 = _dollar_dollar.exists
                    else:
                        _t767 = None
                    return _t767
                _t768 = _t766(msg)
                deconstruct_result154 = _t768
                
                if deconstruct_result154 is not None:
                    _t770 = self.pretty_exists(deconstruct_result154)
                    _t769 = _t770
                else:
                    def _t771(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t772 = _dollar_dollar.reduce
                        else:
                            _t772 = None
                        return _t772
                    _t773 = _t771(msg)
                    deconstruct_result153 = _t773
                    
                    if deconstruct_result153 is not None:
                        _t775 = self.pretty_reduce(deconstruct_result153)
                        _t774 = _t775
                    else:
                        def _t776(_dollar_dollar):
                            _t777 = self.is_empty(_dollar_dollar.conjunction.args)
                            
                            if (_dollar_dollar.HasField('conjunction') and not _t777):
                                _t778 = _dollar_dollar.conjunction
                            else:
                                _t778 = None
                            return _t778
                        _t779 = _t776(msg)
                        deconstruct_result152 = _t779
                        
                        if deconstruct_result152 is not None:
                            _t781 = self.pretty_conjunction(deconstruct_result152)
                            _t780 = _t781
                        else:
                            def _t782(_dollar_dollar):
                                _t783 = self.is_empty(_dollar_dollar.disjunction.args)
                                
                                if (_dollar_dollar.HasField('disjunction') and not _t783):
                                    _t784 = _dollar_dollar.disjunction
                                else:
                                    _t784 = None
                                return _t784
                            _t785 = _t782(msg)
                            deconstruct_result151 = _t785
                            
                            if deconstruct_result151 is not None:
                                _t787 = self.pretty_disjunction(deconstruct_result151)
                                _t786 = _t787
                            else:
                                def _t788(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t789 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t789 = None
                                    return _t789
                                _t790 = _t788(msg)
                                deconstruct_result150 = _t790
                                
                                if deconstruct_result150 is not None:
                                    _t792 = self.pretty_not(deconstruct_result150)
                                    _t791 = _t792
                                else:
                                    def _t793(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t794 = _dollar_dollar.ffi
                                        else:
                                            _t794 = None
                                        return _t794
                                    _t795 = _t793(msg)
                                    deconstruct_result149 = _t795
                                    
                                    if deconstruct_result149 is not None:
                                        _t797 = self.pretty_ffi(deconstruct_result149)
                                        _t796 = _t797
                                    else:
                                        def _t798(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t799 = _dollar_dollar.atom
                                            else:
                                                _t799 = None
                                            return _t799
                                        _t800 = _t798(msg)
                                        deconstruct_result148 = _t800
                                        
                                        if deconstruct_result148 is not None:
                                            _t802 = self.pretty_atom(deconstruct_result148)
                                            _t801 = _t802
                                        else:
                                            def _t803(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t804 = _dollar_dollar.pragma
                                                else:
                                                    _t804 = None
                                                return _t804
                                            _t805 = _t803(msg)
                                            deconstruct_result147 = _t805
                                            
                                            if deconstruct_result147 is not None:
                                                _t807 = self.pretty_pragma(deconstruct_result147)
                                                _t806 = _t807
                                            else:
                                                def _t808(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t809 = _dollar_dollar.primitive
                                                    else:
                                                        _t809 = None
                                                    return _t809
                                                _t810 = _t808(msg)
                                                deconstruct_result146 = _t810
                                                
                                                if deconstruct_result146 is not None:
                                                    _t812 = self.pretty_primitive(deconstruct_result146)
                                                    _t811 = _t812
                                                else:
                                                    def _t813(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t814 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t814 = None
                                                        return _t814
                                                    _t815 = _t813(msg)
                                                    deconstruct_result145 = _t815
                                                    
                                                    if deconstruct_result145 is not None:
                                                        _t817 = self.pretty_rel_atom(deconstruct_result145)
                                                        _t816 = _t817
                                                    else:
                                                        def _t818(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t819 = _dollar_dollar.cast
                                                            else:
                                                                _t819 = None
                                                            return _t819
                                                        _t820 = _t818(msg)
                                                        deconstruct_result144 = _t820
                                                        
                                                        if deconstruct_result144 is not None:
                                                            _t822 = self.pretty_cast(deconstruct_result144)
                                                            _t821 = _t822
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t816 = _t821
                                                    _t811 = _t816
                                                _t806 = _t811
                                            _t801 = _t806
                                        _t796 = _t801
                                    _t791 = _t796
                                _t786 = _t791
                            _t780 = _t786
                        _t774 = _t780
                    _t769 = _t774
                _t764 = _t769
            _t758 = _t764
        return _t758

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t823(_dollar_dollar):
            return _dollar_dollar
        _t824 = _t823(msg)
        fields157 = _t824
        unwrapped_fields158 = fields157
        self.write('(')
        self.write('true')
        self.newline()
        self.indent()
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t825(_dollar_dollar):
            return _dollar_dollar
        _t826 = _t825(msg)
        fields159 = _t826
        unwrapped_fields160 = fields159
        self.write('(')
        self.write('false')
        self.newline()
        self.indent()
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> Optional[Never]:
        def _t827(_dollar_dollar):
            _t828 = Parser.deconstruct_bindings(_dollar_dollar.body)
            return (_t828, _dollar_dollar.body.value,)
        _t829 = _t827(msg)
        fields161 = _t829
        unwrapped_fields162 = fields161
        self.write('(')
        self.write('exists')
        self.newline()
        self.indent()
        field163 = unwrapped_fields162[0]
        _t830 = self.pretty_bindings(field163)
        self.newline()
        field164 = unwrapped_fields162[1]
        _t831 = self.pretty_formula(field164)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[Never]:
        def _t832(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t833 = _t832(msg)
        fields165 = _t833
        unwrapped_fields166 = fields165
        self.write('(')
        self.write('reduce')
        self.newline()
        self.indent()
        field167 = unwrapped_fields166[0]
        _t834 = self.pretty_abstraction(field167)
        self.newline()
        field168 = unwrapped_fields166[1]
        _t835 = self.pretty_abstraction(field168)
        self.newline()
        field169 = unwrapped_fields166[2]
        _t836 = self.pretty_terms(field169)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_terms(self, msg: list[logic_pb2.Term]) -> Optional[Never]:
        def _t837(_dollar_dollar):
            return _dollar_dollar
        _t838 = _t837(msg)
        fields170 = _t838
        unwrapped_fields171 = fields170
        self.write('(')
        self.write('terms')
        self.newline()
        self.indent()
        for i173, elem172 in enumerate(unwrapped_fields171):
            
            if (i173 > 0):
                self.newline()
                _t839 = None
            else:
                _t839 = None
            _t840 = self.pretty_term(elem172)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[Never]:
        def _t841(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t842 = _dollar_dollar.var
            else:
                _t842 = None
            return _t842
        _t843 = _t841(msg)
        deconstruct_result175 = _t843
        
        if deconstruct_result175 is not None:
            _t845 = self.pretty_var(deconstruct_result175)
            _t844 = _t845
        else:
            def _t846(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t847 = _dollar_dollar.constant
                else:
                    _t847 = None
                return _t847
            _t848 = _t846(msg)
            deconstruct_result174 = _t848
            
            if deconstruct_result174 is not None:
                _t850 = self.pretty_constant(deconstruct_result174)
                _t849 = _t850
            else:
                raise ParseError('No matching rule for term')
            _t844 = _t849
        return _t844

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[Never]:
        def _t851(_dollar_dollar):
            return _dollar_dollar.name
        _t852 = _t851(msg)
        fields176 = _t852
        unwrapped_fields177 = fields176
        self.write(unwrapped_fields177)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t853(_dollar_dollar):
            return _dollar_dollar
        _t854 = _t853(msg)
        fields178 = _t854
        unwrapped_fields179 = fields178
        _t855 = self.pretty_value(unwrapped_fields179)
        return _t855

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t856(_dollar_dollar):
            return _dollar_dollar.args
        _t857 = _t856(msg)
        fields180 = _t857
        unwrapped_fields181 = fields180
        self.write('(')
        self.write('and')
        self.newline()
        self.indent()
        for i183, elem182 in enumerate(unwrapped_fields181):
            
            if (i183 > 0):
                self.newline()
                _t858 = None
            else:
                _t858 = None
            _t859 = self.pretty_formula(elem182)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t860(_dollar_dollar):
            return _dollar_dollar.args
        _t861 = _t860(msg)
        fields184 = _t861
        unwrapped_fields185 = fields184
        self.write('(')
        self.write('or')
        self.newline()
        self.indent()
        for i187, elem186 in enumerate(unwrapped_fields185):
            
            if (i187 > 0):
                self.newline()
                _t862 = None
            else:
                _t862 = None
            _t863 = self.pretty_formula(elem186)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[Never]:
        def _t864(_dollar_dollar):
            return _dollar_dollar.arg
        _t865 = _t864(msg)
        fields188 = _t865
        unwrapped_fields189 = fields188
        self.write('(')
        self.write('not')
        self.newline()
        self.indent()
        _t866 = self.pretty_formula(unwrapped_fields189)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[Never]:
        def _t867(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t868 = _t867(msg)
        fields190 = _t868
        unwrapped_fields191 = fields190
        self.write('(')
        self.write('ffi')
        self.newline()
        self.indent()
        field192 = unwrapped_fields191[0]
        _t869 = self.pretty_name(field192)
        self.newline()
        field193 = unwrapped_fields191[1]
        _t870 = self.pretty_ffi_args(field193)
        self.newline()
        field194 = unwrapped_fields191[2]
        _t871 = self.pretty_terms(field194)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_name(self, msg: str) -> Optional[Never]:
        def _t872(_dollar_dollar):
            return _dollar_dollar
        _t873 = _t872(msg)
        fields195 = _t873
        unwrapped_fields196 = fields195
        self.write(':')
        self.write(unwrapped_fields196)
        return None

    def pretty_ffi_args(self, msg: list[logic_pb2.Abstraction]) -> Optional[Never]:
        def _t874(_dollar_dollar):
            return _dollar_dollar
        _t875 = _t874(msg)
        fields197 = _t875
        unwrapped_fields198 = fields197
        self.write('(')
        self.write('args')
        self.newline()
        self.indent()
        for i200, elem199 in enumerate(unwrapped_fields198):
            
            if (i200 > 0):
                self.newline()
                _t876 = None
            else:
                _t876 = None
            _t877 = self.pretty_abstraction(elem199)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[Never]:
        def _t878(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t879 = _t878(msg)
        fields201 = _t879
        unwrapped_fields202 = fields201
        self.write('(')
        self.write('atom')
        self.newline()
        self.indent()
        field203 = unwrapped_fields202[0]
        _t880 = self.pretty_relation_id(field203)
        self.newline()
        field204 = unwrapped_fields202[1]
        for i206, elem205 in enumerate(field204):
            
            if (i206 > 0):
                self.newline()
                _t881 = None
            else:
                _t881 = None
            _t882 = self.pretty_term(elem205)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[Never]:
        def _t883(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t884 = _t883(msg)
        fields207 = _t884
        unwrapped_fields208 = fields207
        self.write('(')
        self.write('pragma')
        self.newline()
        self.indent()
        field209 = unwrapped_fields208[0]
        _t885 = self.pretty_name(field209)
        self.newline()
        field210 = unwrapped_fields208[1]
        for i212, elem211 in enumerate(field210):
            
            if (i212 > 0):
                self.newline()
                _t886 = None
            else:
                _t886 = None
            _t887 = self.pretty_term(elem211)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t888(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t889 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t889 = None
            return _t889
        _t890 = _t888(msg)
        guard_result227 = _t890
        
        if guard_result227 is not None:
            _t892 = self.pretty_eq(msg)
            _t891 = _t892
        else:
            def _t893(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t894 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t894 = None
                return _t894
            _t895 = _t893(msg)
            guard_result226 = _t895
            
            if guard_result226 is not None:
                _t897 = self.pretty_lt(msg)
                _t896 = _t897
            else:
                def _t898(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t899 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t899 = None
                    return _t899
                _t900 = _t898(msg)
                guard_result225 = _t900
                
                if guard_result225 is not None:
                    _t902 = self.pretty_lt_eq(msg)
                    _t901 = _t902
                else:
                    def _t903(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t904 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t904 = None
                        return _t904
                    _t905 = _t903(msg)
                    guard_result224 = _t905
                    
                    if guard_result224 is not None:
                        _t907 = self.pretty_gt(msg)
                        _t906 = _t907
                    else:
                        def _t908(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t909 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t909 = None
                            return _t909
                        _t910 = _t908(msg)
                        guard_result223 = _t910
                        
                        if guard_result223 is not None:
                            _t912 = self.pretty_gt_eq(msg)
                            _t911 = _t912
                        else:
                            def _t913(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t914 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t914 = None
                                return _t914
                            _t915 = _t913(msg)
                            guard_result222 = _t915
                            
                            if guard_result222 is not None:
                                _t917 = self.pretty_add(msg)
                                _t916 = _t917
                            else:
                                def _t918(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t919 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t919 = None
                                    return _t919
                                _t920 = _t918(msg)
                                guard_result221 = _t920
                                
                                if guard_result221 is not None:
                                    _t922 = self.pretty_minus(msg)
                                    _t921 = _t922
                                else:
                                    def _t923(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t924 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t924 = None
                                        return _t924
                                    _t925 = _t923(msg)
                                    guard_result220 = _t925
                                    
                                    if guard_result220 is not None:
                                        _t927 = self.pretty_multiply(msg)
                                        _t926 = _t927
                                    else:
                                        def _t928(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t929 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t929 = None
                                            return _t929
                                        _t930 = _t928(msg)
                                        guard_result219 = _t930
                                        
                                        if guard_result219 is not None:
                                            _t932 = self.pretty_divide(msg)
                                            _t931 = _t932
                                        else:
                                            def _t933(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t934 = _t933(msg)
                                            fields213 = _t934
                                            unwrapped_fields214 = fields213
                                            self.write('(')
                                            self.write('primitive')
                                            self.newline()
                                            self.indent()
                                            field215 = unwrapped_fields214[0]
                                            _t935 = self.pretty_name(field215)
                                            self.newline()
                                            field216 = unwrapped_fields214[1]
                                            for i218, elem217 in enumerate(field216):
                                                
                                                if (i218 > 0):
                                                    self.newline()
                                                    _t936 = None
                                                else:
                                                    _t936 = None
                                                _t937 = self.pretty_rel_term(elem217)
                                            self.dedent()
                                            self.write(')')
                                            self.newline()
                                            _t931 = None
                                        _t926 = _t931
                                    _t921 = _t926
                                _t916 = _t921
                            _t911 = _t916
                        _t906 = _t911
                    _t901 = _t906
                _t896 = _t901
            _t891 = _t896
        return _t891

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t938(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t939 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t939 = None
            return _t939
        _t940 = _t938(msg)
        fields228 = _t940
        unwrapped_fields229 = fields228
        self.write('(')
        self.write('=')
        self.newline()
        self.indent()
        field230 = unwrapped_fields229[0]
        _t941 = self.pretty_term(field230)
        self.newline()
        field231 = unwrapped_fields229[1]
        _t942 = self.pretty_term(field231)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t943(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t944 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t944 = None
            return _t944
        _t945 = _t943(msg)
        fields232 = _t945
        unwrapped_fields233 = fields232
        self.write('(')
        self.write('<')
        self.newline()
        self.indent()
        field234 = unwrapped_fields233[0]
        _t946 = self.pretty_term(field234)
        self.newline()
        field235 = unwrapped_fields233[1]
        _t947 = self.pretty_term(field235)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t948(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t949 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t949 = None
            return _t949
        _t950 = _t948(msg)
        fields236 = _t950
        unwrapped_fields237 = fields236
        self.write('(')
        self.write('<=')
        self.newline()
        self.indent()
        field238 = unwrapped_fields237[0]
        _t951 = self.pretty_term(field238)
        self.newline()
        field239 = unwrapped_fields237[1]
        _t952 = self.pretty_term(field239)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t953(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t954 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t954 = None
            return _t954
        _t955 = _t953(msg)
        fields240 = _t955
        unwrapped_fields241 = fields240
        self.write('(')
        self.write('>')
        self.newline()
        self.indent()
        field242 = unwrapped_fields241[0]
        _t956 = self.pretty_term(field242)
        self.newline()
        field243 = unwrapped_fields241[1]
        _t957 = self.pretty_term(field243)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t958(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t959 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t959 = None
            return _t959
        _t960 = _t958(msg)
        fields244 = _t960
        unwrapped_fields245 = fields244
        self.write('(')
        self.write('>=')
        self.newline()
        self.indent()
        field246 = unwrapped_fields245[0]
        _t961 = self.pretty_term(field246)
        self.newline()
        field247 = unwrapped_fields245[1]
        _t962 = self.pretty_term(field247)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t963(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t964 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t964 = None
            return _t964
        _t965 = _t963(msg)
        fields248 = _t965
        unwrapped_fields249 = fields248
        self.write('(')
        self.write('+')
        self.newline()
        self.indent()
        field250 = unwrapped_fields249[0]
        _t966 = self.pretty_term(field250)
        self.newline()
        field251 = unwrapped_fields249[1]
        _t967 = self.pretty_term(field251)
        self.newline()
        field252 = unwrapped_fields249[2]
        _t968 = self.pretty_term(field252)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t969(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t970 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t970 = None
            return _t970
        _t971 = _t969(msg)
        fields253 = _t971
        unwrapped_fields254 = fields253
        self.write('(')
        self.write('-')
        self.newline()
        self.indent()
        field255 = unwrapped_fields254[0]
        _t972 = self.pretty_term(field255)
        self.newline()
        field256 = unwrapped_fields254[1]
        _t973 = self.pretty_term(field256)
        self.newline()
        field257 = unwrapped_fields254[2]
        _t974 = self.pretty_term(field257)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t975(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t976 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t976 = None
            return _t976
        _t977 = _t975(msg)
        fields258 = _t977
        unwrapped_fields259 = fields258
        self.write('(')
        self.write('*')
        self.newline()
        self.indent()
        field260 = unwrapped_fields259[0]
        _t978 = self.pretty_term(field260)
        self.newline()
        field261 = unwrapped_fields259[1]
        _t979 = self.pretty_term(field261)
        self.newline()
        field262 = unwrapped_fields259[2]
        _t980 = self.pretty_term(field262)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t981(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t982 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t982 = None
            return _t982
        _t983 = _t981(msg)
        fields263 = _t983
        unwrapped_fields264 = fields263
        self.write('(')
        self.write('/')
        self.newline()
        self.indent()
        field265 = unwrapped_fields264[0]
        _t984 = self.pretty_term(field265)
        self.newline()
        field266 = unwrapped_fields264[1]
        _t985 = self.pretty_term(field266)
        self.newline()
        field267 = unwrapped_fields264[2]
        _t986 = self.pretty_term(field267)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[Never]:
        def _t987(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t988 = _dollar_dollar.specialized_value
            else:
                _t988 = None
            return _t988
        _t989 = _t987(msg)
        deconstruct_result269 = _t989
        
        if deconstruct_result269 is not None:
            _t991 = self.pretty_specialized_value(deconstruct_result269)
            _t990 = _t991
        else:
            def _t992(_dollar_dollar):
                
                if _dollar_dollar.HasField('var'):
                    _t993 = _dollar_dollar.var
                else:
                    _t993 = None
                return _t993
            _t994 = _t992(msg)
            guard_result268 = _t994
            
            if guard_result268 is not None:
                _t996 = self.pretty_term(msg)
                _t995 = _t996
            else:
                raise ParseError('No matching rule for rel_term')
            _t990 = _t995
        return _t990

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t997(_dollar_dollar):
            return _dollar_dollar
        _t998 = _t997(msg)
        fields270 = _t998
        unwrapped_fields271 = fields270
        self.write('#')
        _t999 = self.pretty_value(unwrapped_fields271)
        return _t999

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[Never]:
        def _t1000(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1001 = _t1000(msg)
        fields272 = _t1001
        unwrapped_fields273 = fields272
        self.write('(')
        self.write('relatom')
        self.newline()
        self.indent()
        field274 = unwrapped_fields273[0]
        _t1002 = self.pretty_name(field274)
        self.newline()
        field275 = unwrapped_fields273[1]
        for i277, elem276 in enumerate(field275):
            
            if (i277 > 0):
                self.newline()
                _t1003 = None
            else:
                _t1003 = None
            _t1004 = self.pretty_rel_term(elem276)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[Never]:
        def _t1005(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t1006 = _t1005(msg)
        fields278 = _t1006
        unwrapped_fields279 = fields278
        self.write('(')
        self.write('cast')
        self.newline()
        self.indent()
        field280 = unwrapped_fields279[0]
        _t1007 = self.pretty_term(field280)
        self.newline()
        field281 = unwrapped_fields279[1]
        _t1008 = self.pretty_term(field281)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_attrs(self, msg: list[logic_pb2.Attribute]) -> Optional[Never]:
        def _t1009(_dollar_dollar):
            return _dollar_dollar
        _t1010 = _t1009(msg)
        fields282 = _t1010
        unwrapped_fields283 = fields282
        self.write('(')
        self.write('attrs')
        self.newline()
        self.indent()
        for i285, elem284 in enumerate(unwrapped_fields283):
            
            if (i285 > 0):
                self.newline()
                _t1011 = None
            else:
                _t1011 = None
            _t1012 = self.pretty_attribute(elem284)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[Never]:
        def _t1013(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t1014 = _t1013(msg)
        fields286 = _t1014
        unwrapped_fields287 = fields286
        self.write('(')
        self.write('attribute')
        self.newline()
        self.indent()
        field288 = unwrapped_fields287[0]
        _t1015 = self.pretty_name(field288)
        self.newline()
        field289 = unwrapped_fields287[1]
        for i291, elem290 in enumerate(field289):
            
            if (i291 > 0):
                self.newline()
                _t1016 = None
            else:
                _t1016 = None
            _t1017 = self.pretty_value(elem290)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[Never]:
        def _t1018(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t1019 = _t1018(msg)
        fields292 = _t1019
        unwrapped_fields293 = fields292
        self.write('(')
        self.write('algorithm')
        self.newline()
        self.indent()
        field294 = unwrapped_fields293[0]
        for i296, elem295 in enumerate(field294):
            
            if (i296 > 0):
                self.newline()
                _t1020 = None
            else:
                _t1020 = None
            _t1021 = self.pretty_relation_id(elem295)
        self.newline()
        field297 = unwrapped_fields293[1]
        _t1022 = self.pretty_script(field297)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[Never]:
        def _t1023(_dollar_dollar):
            return _dollar_dollar.constructs
        _t1024 = _t1023(msg)
        fields298 = _t1024
        unwrapped_fields299 = fields298
        self.write('(')
        self.write('script')
        self.newline()
        self.indent()
        for i301, elem300 in enumerate(unwrapped_fields299):
            
            if (i301 > 0):
                self.newline()
                _t1025 = None
            else:
                _t1025 = None
            _t1026 = self.pretty_construct(elem300)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[Never]:
        def _t1027(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t1028 = _dollar_dollar.loop
            else:
                _t1028 = None
            return _t1028
        _t1029 = _t1027(msg)
        deconstruct_result303 = _t1029
        
        if deconstruct_result303 is not None:
            _t1031 = self.pretty_loop(deconstruct_result303)
            _t1030 = _t1031
        else:
            def _t1032(_dollar_dollar):
                
                if _dollar_dollar.HasField('assign'):
                    _t1033 = _dollar_dollar.assign
                else:
                    _t1033 = None
                return _t1033
            _t1034 = _t1032(msg)
            guard_result302 = _t1034
            
            if guard_result302 is not None:
                _t1036 = self.pretty_instruction(msg)
                _t1035 = _t1036
            else:
                raise ParseError('No matching rule for construct')
            _t1030 = _t1035
        return _t1030

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[Never]:
        def _t1037(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1038 = _t1037(msg)
        fields304 = _t1038
        unwrapped_fields305 = fields304
        self.write('(')
        self.write('loop')
        self.newline()
        self.indent()
        field306 = unwrapped_fields305[0]
        _t1039 = self.pretty_init(field306)
        self.newline()
        field307 = unwrapped_fields305[1]
        _t1040 = self.pretty_script(field307)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_init(self, msg: list[logic_pb2.Instruction]) -> Optional[Never]:
        def _t1041(_dollar_dollar):
            return _dollar_dollar
        _t1042 = _t1041(msg)
        fields308 = _t1042
        unwrapped_fields309 = fields308
        self.write('(')
        self.write('init')
        self.newline()
        self.indent()
        for i311, elem310 in enumerate(unwrapped_fields309):
            
            if (i311 > 0):
                self.newline()
                _t1043 = None
            else:
                _t1043 = None
            _t1044 = self.pretty_instruction(elem310)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[Never]:
        def _t1045(_dollar_dollar):
            _t1046 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t1046:
                _t1047 = (_dollar_dollar.name, _dollar_dollar.body, _dollar_dollar.attrs,)
            else:
                _t1047 = None
            return _t1047
        _t1048 = _t1045(msg)
        guard_result316 = _t1048
        
        if guard_result316 is not None:
            _t1050 = self.pretty_assign(msg)
            _t1049 = _t1050
        else:
            def _t1051(_dollar_dollar):
                _t1052 = self.is_empty(_dollar_dollar.attrs)
                
                if not _t1052:
                    _t1053 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _dollar_dollar.attrs,)
                else:
                    _t1053 = None
                return _t1053
            _t1054 = _t1051(msg)
            guard_result315 = _t1054
            
            if guard_result315 is not None:
                _t1056 = self.pretty_upsert(msg)
                _t1055 = _t1056
            else:
                def _t1057(_dollar_dollar):
                    _t1058 = self.is_empty(_dollar_dollar.attrs)
                    
                    if not _t1058:
                        _t1059 = (_dollar_dollar.name, _dollar_dollar.body, _dollar_dollar.attrs,)
                    else:
                        _t1059 = None
                    return _t1059
                _t1060 = _t1057(msg)
                guard_result314 = _t1060
                
                if guard_result314 is not None:
                    _t1062 = self.pretty_break(msg)
                    _t1061 = _t1062
                else:
                    def _t1063(_dollar_dollar):
                        _t1064 = self.is_empty(_dollar_dollar.attrs)
                        
                        if not _t1064:
                            _t1065 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _dollar_dollar.attrs,)
                        else:
                            _t1065 = None
                        return _t1065
                    _t1066 = _t1063(msg)
                    guard_result313 = _t1066
                    
                    if guard_result313 is not None:
                        _t1068 = self.pretty_monoid_def(msg)
                        _t1067 = _t1068
                    else:
                        def _t1069(_dollar_dollar):
                            _t1070 = self.is_empty(_dollar_dollar.attrs)
                            
                            if not _t1070:
                                _t1071 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _dollar_dollar.attrs,)
                            else:
                                _t1071 = None
                            return _t1071
                        _t1072 = _t1069(msg)
                        guard_result312 = _t1072
                        
                        if guard_result312 is not None:
                            _t1074 = self.pretty_monus_def(msg)
                            _t1073 = _t1074
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1067 = _t1073
                    _t1061 = _t1067
                _t1055 = _t1061
            _t1049 = _t1055
        return _t1049

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[Never]:
        def _t1075(_dollar_dollar):
            _t1076 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t1076:
                _t1077 = (_dollar_dollar.name, _dollar_dollar.body, _dollar_dollar.attrs,)
            else:
                _t1077 = None
            return _t1077
        _t1078 = _t1075(msg)
        fields317 = _t1078
        unwrapped_fields318 = fields317
        self.write('(')
        self.write('assign')
        self.newline()
        self.indent()
        field319 = unwrapped_fields318[0]
        _t1079 = self.pretty_relation_id(field319)
        self.newline()
        field320 = unwrapped_fields318[1]
        _t1080 = self.pretty_abstraction(field320)
        self.newline()
        field321 = unwrapped_fields318[2]
        
        if field321 is not None:
            opt_val322 = field321
            _t1082 = self.pretty_attrs(opt_val322)
            _t1081 = _t1082
        else:
            _t1081 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[Never]:
        def _t1083(_dollar_dollar):
            _t1084 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t1084:
                _t1085 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _dollar_dollar.attrs,)
            else:
                _t1085 = None
            return _t1085
        _t1086 = _t1083(msg)
        fields323 = _t1086
        unwrapped_fields324 = fields323
        self.write('(')
        self.write('upsert')
        self.newline()
        self.indent()
        field325 = unwrapped_fields324[0]
        _t1087 = self.pretty_relation_id(field325)
        self.newline()
        field326 = unwrapped_fields324[1]
        _t1088 = self.pretty_abstraction_with_arity(field326)
        self.newline()
        field327 = unwrapped_fields324[2]
        
        if field327 is not None:
            opt_val328 = field327
            _t1090 = self.pretty_attrs(opt_val328)
            _t1089 = _t1090
        else:
            _t1089 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[Never]:
        def _t1091(_dollar_dollar):
            _t1092 = Parser.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1092, _dollar_dollar[0].value,)
        _t1093 = _t1091(msg)
        fields329 = _t1093
        unwrapped_fields330 = fields329
        self.write('(')
        field331 = unwrapped_fields330[0]
        _t1094 = self.pretty_bindings(field331)
        field332 = unwrapped_fields330[1]
        _t1095 = self.pretty_formula(field332)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[Never]:
        def _t1096(_dollar_dollar):
            _t1097 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t1097:
                _t1098 = (_dollar_dollar.name, _dollar_dollar.body, _dollar_dollar.attrs,)
            else:
                _t1098 = None
            return _t1098
        _t1099 = _t1096(msg)
        fields333 = _t1099
        unwrapped_fields334 = fields333
        self.write('(')
        self.write('break')
        self.newline()
        self.indent()
        field335 = unwrapped_fields334[0]
        _t1100 = self.pretty_relation_id(field335)
        self.newline()
        field336 = unwrapped_fields334[1]
        _t1101 = self.pretty_abstraction(field336)
        self.newline()
        field337 = unwrapped_fields334[2]
        
        if field337 is not None:
            opt_val338 = field337
            _t1103 = self.pretty_attrs(opt_val338)
            _t1102 = _t1103
        else:
            _t1102 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[Never]:
        def _t1104(_dollar_dollar):
            _t1105 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t1105:
                _t1106 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _dollar_dollar.attrs,)
            else:
                _t1106 = None
            return _t1106
        _t1107 = _t1104(msg)
        fields339 = _t1107
        unwrapped_fields340 = fields339
        self.write('(')
        self.write('monoid')
        self.newline()
        self.indent()
        field341 = unwrapped_fields340[0]
        _t1108 = self.pretty_monoid(field341)
        self.newline()
        field342 = unwrapped_fields340[1]
        _t1109 = self.pretty_relation_id(field342)
        self.newline()
        field343 = unwrapped_fields340[2]
        _t1110 = self.pretty_abstraction_with_arity(field343)
        self.newline()
        field344 = unwrapped_fields340[3]
        
        if field344 is not None:
            opt_val345 = field344
            _t1112 = self.pretty_attrs(opt_val345)
            _t1111 = _t1112
        else:
            _t1111 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[Never]:
        def _t1113(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1114 = _dollar_dollar.or_monoid
            else:
                _t1114 = None
            return _t1114
        _t1115 = _t1113(msg)
        deconstruct_result349 = _t1115
        
        if deconstruct_result349 is not None:
            _t1117 = self.pretty_or_monoid(deconstruct_result349)
            _t1116 = _t1117
        else:
            def _t1118(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1119 = _dollar_dollar.min_monoid
                else:
                    _t1119 = None
                return _t1119
            _t1120 = _t1118(msg)
            deconstruct_result348 = _t1120
            
            if deconstruct_result348 is not None:
                _t1122 = self.pretty_min_monoid(deconstruct_result348)
                _t1121 = _t1122
            else:
                def _t1123(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1124 = _dollar_dollar.max_monoid
                    else:
                        _t1124 = None
                    return _t1124
                _t1125 = _t1123(msg)
                deconstruct_result347 = _t1125
                
                if deconstruct_result347 is not None:
                    _t1127 = self.pretty_max_monoid(deconstruct_result347)
                    _t1126 = _t1127
                else:
                    def _t1128(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1129 = _dollar_dollar.sum_monoid
                        else:
                            _t1129 = None
                        return _t1129
                    _t1130 = _t1128(msg)
                    deconstruct_result346 = _t1130
                    
                    if deconstruct_result346 is not None:
                        _t1132 = self.pretty_sum_monoid(deconstruct_result346)
                        _t1131 = _t1132
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1126 = _t1131
                _t1121 = _t1126
            _t1116 = _t1121
        return _t1116

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[Never]:
        def _t1133(_dollar_dollar):
            return _dollar_dollar
        _t1134 = _t1133(msg)
        fields350 = _t1134
        unwrapped_fields351 = fields350
        self.write('(')
        self.write('or')
        self.newline()
        self.indent()
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> Optional[Never]:
        def _t1135(_dollar_dollar):
            return _dollar_dollar.type
        _t1136 = _t1135(msg)
        fields352 = _t1136
        unwrapped_fields353 = fields352
        self.write('(')
        self.write('min')
        self.newline()
        self.indent()
        _t1137 = self.pretty_type(unwrapped_fields353)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[Never]:
        def _t1138(_dollar_dollar):
            return _dollar_dollar.type
        _t1139 = _t1138(msg)
        fields354 = _t1139
        unwrapped_fields355 = fields354
        self.write('(')
        self.write('max')
        self.newline()
        self.indent()
        _t1140 = self.pretty_type(unwrapped_fields355)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[Never]:
        def _t1141(_dollar_dollar):
            return _dollar_dollar.type
        _t1142 = _t1141(msg)
        fields356 = _t1142
        unwrapped_fields357 = fields356
        self.write('(')
        self.write('sum')
        self.newline()
        self.indent()
        _t1143 = self.pretty_type(unwrapped_fields357)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[Never]:
        def _t1144(_dollar_dollar):
            _t1145 = self.is_empty(_dollar_dollar.attrs)
            
            if not _t1145:
                _t1146 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _dollar_dollar.attrs,)
            else:
                _t1146 = None
            return _t1146
        _t1147 = _t1144(msg)
        fields358 = _t1147
        unwrapped_fields359 = fields358
        self.write('(')
        self.write('monus')
        self.newline()
        self.indent()
        field360 = unwrapped_fields359[0]
        _t1148 = self.pretty_monoid(field360)
        self.newline()
        field361 = unwrapped_fields359[1]
        _t1149 = self.pretty_relation_id(field361)
        self.newline()
        field362 = unwrapped_fields359[2]
        _t1150 = self.pretty_abstraction_with_arity(field362)
        self.newline()
        field363 = unwrapped_fields359[3]
        
        if field363 is not None:
            opt_val364 = field363
            _t1152 = self.pretty_attrs(opt_val364)
            _t1151 = _t1152
        else:
            _t1151 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[Never]:
        def _t1153(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1154 = _t1153(msg)
        fields365 = _t1154
        unwrapped_fields366 = fields365
        self.write('(')
        self.write('functional_dependency')
        self.newline()
        self.indent()
        field367 = unwrapped_fields366[0]
        _t1155 = self.pretty_relation_id(field367)
        self.newline()
        field368 = unwrapped_fields366[1]
        _t1156 = self.pretty_abstraction(field368)
        self.newline()
        field369 = unwrapped_fields366[2]
        _t1157 = self.pretty_functional_dependency_keys(field369)
        self.newline()
        field370 = unwrapped_fields366[3]
        _t1158 = self.pretty_functional_dependency_values(field370)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_functional_dependency_keys(self, msg: list[logic_pb2.Var]) -> Optional[Never]:
        def _t1159(_dollar_dollar):
            return _dollar_dollar
        _t1160 = _t1159(msg)
        fields371 = _t1160
        unwrapped_fields372 = fields371
        self.write('(')
        self.write('keys')
        self.newline()
        self.indent()
        for i374, elem373 in enumerate(unwrapped_fields372):
            
            if (i374 > 0):
                self.newline()
                _t1161 = None
            else:
                _t1161 = None
            _t1162 = self.pretty_var(elem373)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_functional_dependency_values(self, msg: list[logic_pb2.Var]) -> Optional[Never]:
        def _t1163(_dollar_dollar):
            return _dollar_dollar
        _t1164 = _t1163(msg)
        fields375 = _t1164
        unwrapped_fields376 = fields375
        self.write('(')
        self.write('values')
        self.newline()
        self.indent()
        for i378, elem377 in enumerate(unwrapped_fields376):
            
            if (i378 > 0):
                self.newline()
                _t1165 = None
            else:
                _t1165 = None
            _t1166 = self.pretty_var(elem377)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[Never]:
        def _t1167(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1168 = _dollar_dollar.rel_edb
            else:
                _t1168 = None
            return _t1168
        _t1169 = _t1167(msg)
        deconstruct_result381 = _t1169
        
        if deconstruct_result381 is not None:
            _t1171 = self.pretty_rel_edb(deconstruct_result381)
            _t1170 = _t1171
        else:
            def _t1172(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1173 = _dollar_dollar.betree_relation
                else:
                    _t1173 = None
                return _t1173
            _t1174 = _t1172(msg)
            deconstruct_result380 = _t1174
            
            if deconstruct_result380 is not None:
                _t1176 = self.pretty_betree_relation(deconstruct_result380)
                _t1175 = _t1176
            else:
                def _t1177(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1178 = _dollar_dollar.csv_data
                    else:
                        _t1178 = None
                    return _t1178
                _t1179 = _t1177(msg)
                deconstruct_result379 = _t1179
                
                if deconstruct_result379 is not None:
                    _t1181 = self.pretty_csv_data(deconstruct_result379)
                    _t1180 = _t1181
                else:
                    raise ParseError('No matching rule for data')
                _t1175 = _t1180
            _t1170 = _t1175
        return _t1170

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[Never]:
        def _t1182(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1183 = _t1182(msg)
        fields382 = _t1183
        unwrapped_fields383 = fields382
        self.write('(')
        self.write('rel_edb')
        self.newline()
        self.indent()
        field384 = unwrapped_fields383[0]
        _t1184 = self.pretty_relation_id(field384)
        self.newline()
        field385 = unwrapped_fields383[1]
        _t1185 = self.pretty_rel_edb_path(field385)
        self.newline()
        field386 = unwrapped_fields383[2]
        _t1186 = self.pretty_rel_edb_types(field386)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_rel_edb_path(self, msg: list[str]) -> Optional[Never]:
        def _t1187(_dollar_dollar):
            return _dollar_dollar
        _t1188 = _t1187(msg)
        fields387 = _t1188
        unwrapped_fields388 = fields387
        self.write('[')
        for i390, elem389 in enumerate(unwrapped_fields388):
            
            if (i390 > 0):
                self.newline()
                _t1189 = None
            else:
                _t1189 = None
            self.write(repr(elem389))
        self.write(']')
        return None

    def pretty_rel_edb_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1190(_dollar_dollar):
            return _dollar_dollar
        _t1191 = _t1190(msg)
        fields391 = _t1191
        unwrapped_fields392 = fields391
        self.write('[')
        for i394, elem393 in enumerate(unwrapped_fields392):
            
            if (i394 > 0):
                self.newline()
                _t1192 = None
            else:
                _t1192 = None
            _t1193 = self.pretty_type(elem393)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[Never]:
        def _t1194(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1195 = _t1194(msg)
        fields395 = _t1195
        unwrapped_fields396 = fields395
        self.write('(')
        self.write('betree_relation')
        self.newline()
        self.indent()
        field397 = unwrapped_fields396[0]
        _t1196 = self.pretty_relation_id(field397)
        self.newline()
        field398 = unwrapped_fields396[1]
        _t1197 = self.pretty_betree_info(field398)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[Never]:
        def _t1198(_dollar_dollar):
            _t1199 = Parser.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1199,)
        _t1200 = _t1198(msg)
        fields399 = _t1200
        unwrapped_fields400 = fields399
        self.write('(')
        self.write('betree_info')
        self.newline()
        self.indent()
        field401 = unwrapped_fields400[0]
        _t1201 = self.pretty_betree_info_key_types(field401)
        self.newline()
        field402 = unwrapped_fields400[1]
        _t1202 = self.pretty_betree_info_value_types(field402)
        self.newline()
        field403 = unwrapped_fields400[2]
        _t1203 = self.pretty_config_dict(field403)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_betree_info_key_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1204(_dollar_dollar):
            return _dollar_dollar
        _t1205 = _t1204(msg)
        fields404 = _t1205
        unwrapped_fields405 = fields404
        self.write('(')
        self.write('key_types')
        self.newline()
        self.indent()
        for i407, elem406 in enumerate(unwrapped_fields405):
            
            if (i407 > 0):
                self.newline()
                _t1206 = None
            else:
                _t1206 = None
            _t1207 = self.pretty_type(elem406)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_betree_info_value_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1208(_dollar_dollar):
            return _dollar_dollar
        _t1209 = _t1208(msg)
        fields408 = _t1209
        unwrapped_fields409 = fields408
        self.write('(')
        self.write('value_types')
        self.newline()
        self.indent()
        for i411, elem410 in enumerate(unwrapped_fields409):
            
            if (i411 > 0):
                self.newline()
                _t1210 = None
            else:
                _t1210 = None
            _t1211 = self.pretty_type(elem410)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[Never]:
        def _t1212(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1213 = _t1212(msg)
        fields412 = _t1213
        unwrapped_fields413 = fields412
        self.write('(')
        self.write('csv_data')
        self.newline()
        self.indent()
        field414 = unwrapped_fields413[0]
        _t1214 = self.pretty_csvlocator(field414)
        self.newline()
        field415 = unwrapped_fields413[1]
        _t1215 = self.pretty_csv_config(field415)
        self.newline()
        field416 = unwrapped_fields413[2]
        _t1216 = self.pretty_csv_columns(field416)
        self.newline()
        field417 = unwrapped_fields413[3]
        _t1217 = self.pretty_csv_asof(field417)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[Never]:
        def _t1218(_dollar_dollar):
            _t1219 = self.is_empty(_dollar_dollar.paths)
            _t1220 = self.decode_string(_dollar_dollar.inline_data)
            
            if (not _t1219 and _t1220 != ''):
                _t1222 = self.decode_string(_dollar_dollar.inline_data)
                _t1221 = (_dollar_dollar.paths, _t1222,)
            else:
                _t1221 = None
            return _t1221
        _t1223 = _t1218(msg)
        fields418 = _t1223
        unwrapped_fields419 = fields418
        self.write('(')
        self.write('csv_locator')
        self.newline()
        self.indent()
        field420 = unwrapped_fields419[0]
        
        if field420 is not None:
            opt_val421 = field420
            _t1225 = self.pretty_csv_locator_paths(opt_val421)
            _t1224 = _t1225
        else:
            _t1224 = None
        self.newline()
        field422 = unwrapped_fields419[1]
        
        if field422 is not None:
            opt_val423 = field422
            _t1227 = self.pretty_csv_locator_inline_data(opt_val423)
            _t1226 = _t1227
        else:
            _t1226 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_locator_paths(self, msg: list[str]) -> Optional[Never]:
        def _t1228(_dollar_dollar):
            return _dollar_dollar
        _t1229 = _t1228(msg)
        fields424 = _t1229
        unwrapped_fields425 = fields424
        self.write('(')
        self.write('paths')
        self.newline()
        self.indent()
        for i427, elem426 in enumerate(unwrapped_fields425):
            
            if (i427 > 0):
                self.newline()
                _t1230 = None
            else:
                _t1230 = None
            self.write(repr(elem426))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> Optional[Never]:
        def _t1231(_dollar_dollar):
            return _dollar_dollar
        _t1232 = _t1231(msg)
        fields428 = _t1232
        unwrapped_fields429 = fields428
        self.write('(')
        self.write('inline_data')
        self.newline()
        self.indent()
        self.write(repr(unwrapped_fields429))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> Optional[Never]:
        def _t1233(_dollar_dollar):
            _t1234 = Parser.deconstruct_csv_config(_dollar_dollar)
            return _t1234
        _t1235 = _t1233(msg)
        fields430 = _t1235
        unwrapped_fields431 = fields430
        self.write('(')
        self.write('csv_config')
        self.newline()
        self.indent()
        _t1236 = self.pretty_config_dict(unwrapped_fields431)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_columns(self, msg: list[logic_pb2.CSVColumn]) -> Optional[Never]:
        def _t1237(_dollar_dollar):
            return _dollar_dollar
        _t1238 = _t1237(msg)
        fields432 = _t1238
        unwrapped_fields433 = fields432
        self.write('(')
        self.write('columns')
        self.newline()
        self.indent()
        for i435, elem434 in enumerate(unwrapped_fields433):
            
            if (i435 > 0):
                self.newline()
                _t1239 = None
            else:
                _t1239 = None
            _t1240 = self.pretty_csv_column(elem434)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[Never]:
        def _t1241(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1242 = _t1241(msg)
        fields436 = _t1242
        unwrapped_fields437 = fields436
        self.write('(')
        self.write('column')
        self.newline()
        self.indent()
        field438 = unwrapped_fields437[0]
        self.write(repr(field438))
        self.newline()
        field439 = unwrapped_fields437[1]
        _t1243 = self.pretty_relation_id(field439)
        self.write('[')
        self.newline()
        field440 = unwrapped_fields437[2]
        for i442, elem441 in enumerate(field440):
            
            if (i442 > 0):
                self.newline()
                _t1244 = None
            else:
                _t1244 = None
            _t1245 = self.pretty_type(elem441)
        self.write(']')
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[Never]:
        def _t1246(_dollar_dollar):
            return _dollar_dollar
        _t1247 = _t1246(msg)
        fields443 = _t1247
        unwrapped_fields444 = fields443
        self.write('(')
        self.write('asof')
        self.newline()
        self.indent()
        self.write(repr(unwrapped_fields444))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> Optional[Never]:
        def _t1248(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1249 = _t1248(msg)
        fields445 = _t1249
        unwrapped_fields446 = fields445
        self.write('(')
        self.write('undefine')
        self.newline()
        self.indent()
        _t1250 = self.pretty_fragment_id(unwrapped_fields446)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[Never]:
        def _t1251(_dollar_dollar):
            return _dollar_dollar.relations
        _t1252 = _t1251(msg)
        fields447 = _t1252
        unwrapped_fields448 = fields447
        self.write('(')
        self.write('context')
        self.newline()
        self.indent()
        for i450, elem449 in enumerate(unwrapped_fields448):
            
            if (i450 > 0):
                self.newline()
                _t1253 = None
            else:
                _t1253 = None
            _t1254 = self.pretty_relation_id(elem449)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_epoch_reads(self, msg: list[transactions_pb2.Read]) -> Optional[Never]:
        def _t1255(_dollar_dollar):
            return _dollar_dollar
        _t1256 = _t1255(msg)
        fields451 = _t1256
        unwrapped_fields452 = fields451
        self.write('(')
        self.write('reads')
        self.newline()
        self.indent()
        for i454, elem453 in enumerate(unwrapped_fields452):
            
            if (i454 > 0):
                self.newline()
                _t1257 = None
            else:
                _t1257 = None
            _t1258 = self.pretty_read(elem453)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[Never]:
        def _t1259(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1260 = _dollar_dollar.demand
            else:
                _t1260 = None
            return _t1260
        _t1261 = _t1259(msg)
        deconstruct_result459 = _t1261
        
        if deconstruct_result459 is not None:
            _t1263 = self.pretty_demand(deconstruct_result459)
            _t1262 = _t1263
        else:
            def _t1264(_dollar_dollar):
                
                if _dollar_dollar.name != 'output':
                    _t1265 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
                else:
                    _t1265 = None
                return _t1265
            _t1266 = _t1264(msg)
            guard_result458 = _t1266
            
            if guard_result458 is not None:
                _t1268 = self.pretty_output(msg)
                _t1267 = _t1268
            else:
                def _t1269(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1270 = _dollar_dollar.what_if
                    else:
                        _t1270 = None
                    return _t1270
                _t1271 = _t1269(msg)
                deconstruct_result457 = _t1271
                
                if deconstruct_result457 is not None:
                    _t1273 = self.pretty_what_if(deconstruct_result457)
                    _t1272 = _t1273
                else:
                    def _t1274(_dollar_dollar):
                        
                        if _dollar_dollar.name != 'abort':
                            _t1275 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
                        else:
                            _t1275 = None
                        return _t1275
                    _t1276 = _t1274(msg)
                    guard_result456 = _t1276
                    
                    if guard_result456 is not None:
                        _t1278 = self.pretty_abort(msg)
                        _t1277 = _t1278
                    else:
                        def _t1279(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1280 = _dollar_dollar.export
                            else:
                                _t1280 = None
                            return _t1280
                        _t1281 = _t1279(msg)
                        deconstruct_result455 = _t1281
                        
                        if deconstruct_result455 is not None:
                            _t1283 = self.pretty_export(deconstruct_result455)
                            _t1282 = _t1283
                        else:
                            raise ParseError('No matching rule for read')
                        _t1277 = _t1282
                    _t1272 = _t1277
                _t1267 = _t1272
            _t1262 = _t1267
        return _t1262

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[Never]:
        def _t1284(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1285 = _t1284(msg)
        fields460 = _t1285
        unwrapped_fields461 = fields460
        self.write('(')
        self.write('demand')
        self.newline()
        self.indent()
        _t1286 = self.pretty_relation_id(unwrapped_fields461)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[Never]:
        def _t1287(_dollar_dollar):
            
            if _dollar_dollar.name != 'output':
                _t1288 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            else:
                _t1288 = None
            return _t1288
        _t1289 = _t1287(msg)
        fields462 = _t1289
        unwrapped_fields463 = fields462
        self.write('(')
        self.write('output')
        self.newline()
        self.indent()
        field464 = unwrapped_fields463[0]
        
        if field464 is not None:
            opt_val465 = field464
            _t1291 = self.pretty_name(opt_val465)
            _t1290 = _t1291
        else:
            _t1290 = None
        self.newline()
        field466 = unwrapped_fields463[1]
        _t1292 = self.pretty_relation_id(field466)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[Never]:
        def _t1293(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1294 = _t1293(msg)
        fields467 = _t1294
        unwrapped_fields468 = fields467
        self.write('(')
        self.write('what_if')
        self.newline()
        self.indent()
        field469 = unwrapped_fields468[0]
        _t1295 = self.pretty_name(field469)
        self.newline()
        field470 = unwrapped_fields468[1]
        _t1296 = self.pretty_epoch(field470)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[Never]:
        def _t1297(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1298 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            else:
                _t1298 = None
            return _t1298
        _t1299 = _t1297(msg)
        fields471 = _t1299
        unwrapped_fields472 = fields471
        self.write('(')
        self.write('abort')
        self.newline()
        self.indent()
        field473 = unwrapped_fields472[0]
        
        if field473 is not None:
            opt_val474 = field473
            _t1301 = self.pretty_name(opt_val474)
            _t1300 = _t1301
        else:
            _t1300 = None
        self.newline()
        field475 = unwrapped_fields472[1]
        _t1302 = self.pretty_relation_id(field475)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[Never]:
        def _t1303(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1304 = _t1303(msg)
        fields476 = _t1304
        unwrapped_fields477 = fields476
        self.write('(')
        self.write('export')
        self.newline()
        self.indent()
        _t1305 = self.pretty_export_csv_config(unwrapped_fields477)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[Never]:
        def _t1306(_dollar_dollar):
            _t1307 = Parser.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1307,)
        _t1308 = _t1306(msg)
        fields478 = _t1308
        unwrapped_fields479 = fields478
        self.write('(')
        self.write('export_csv_config')
        self.newline()
        self.indent()
        field480 = unwrapped_fields479[0]
        _t1309 = self.pretty_export_csv_path(field480)
        self.newline()
        field481 = unwrapped_fields479[1]
        _t1310 = self.pretty_export_csv_columns(field481)
        self.newline()
        field482 = unwrapped_fields479[2]
        _t1311 = self.pretty_config_dict(field482)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[Never]:
        def _t1312(_dollar_dollar):
            return _dollar_dollar
        _t1313 = _t1312(msg)
        fields483 = _t1313
        unwrapped_fields484 = fields483
        self.write('(')
        self.write('path')
        self.newline()
        self.indent()
        self.write(repr(unwrapped_fields484))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_columns(self, msg: list[transactions_pb2.ExportCSVColumn]) -> Optional[Never]:
        def _t1314(_dollar_dollar):
            return _dollar_dollar
        _t1315 = _t1314(msg)
        fields485 = _t1315
        unwrapped_fields486 = fields485
        self.write('(')
        self.write('columns')
        self.newline()
        self.indent()
        for i488, elem487 in enumerate(unwrapped_fields486):
            
            if (i488 > 0):
                self.newline()
                _t1316 = None
            else:
                _t1316 = None
            _t1317 = self.pretty_export_csv_column(elem487)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[Never]:
        def _t1318(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1319 = _t1318(msg)
        fields489 = _t1319
        unwrapped_fields490 = fields489
        self.write('(')
        self.write('column')
        self.newline()
        self.indent()
        field491 = unwrapped_fields490[0]
        self.write(repr(field491))
        self.newline()
        field492 = unwrapped_fields490[1]
        _t1320 = self.pretty_relation_id(field492)
        self.dedent()
        self.write(')')
        self.newline()
        return None


def pretty(msg: Any, io: IO[str] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    return printer.get_output()
