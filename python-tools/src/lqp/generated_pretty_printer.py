"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli proto/relationalai/lqp/v1/fragments.proto proto/relationalai/lqp/v1/logic.proto proto/relationalai/lqp/v1/transactions.proto --grammar python-tools/src/meta/grammar.y --printer python
"""

from io import StringIO
from typing import Any, IO, Never, Optional

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: Optional[IO[str]] = None):
        self.io = io if io is not None else StringIO()
        self.indent_level = 0
        self.at_line_start = True
        self._debug_info: dict[tuple[int, int], str] = {}

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

    def start_pretty_fragment(self, msg) -> None:
        """Extract debug info from Fragment for relation ID lookup."""
        debug_info = msg.debug_info
        for rid, name in zip(debug_info.ids, debug_info.orig_names):
            self._debug_info[(rid.id_low, rid.id_high)] = name

    def relation_id_to_string(self, msg) -> str:
        """Convert RelationId to string representation using debug info."""
        return self._debug_info.get((msg.id_low, msg.id_high), "")

    def relation_id_to_int(self, msg):
        """Convert RelationId to int representation if it has id."""
        if msg.id_low or msg.id_high:
            return (msg.id_high << 64) | msg.id_low
        return None

    def relation_id_to_uint128(self, msg):
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> Optional[Never]:
        def _t493(_dollar_dollar):
            _t494 = self.is_default_configure(_dollar_dollar.configure)
            
            if not _t494:
                _t495 = _dollar_dollar.configure
            else:
                _t495 = None
            return (_t495, _dollar_dollar.sync, _dollar_dollar.epochs,)
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
            _t504 = self.deconstruct_configure(_dollar_dollar)
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
                                self.write(self.format_uint128(deconstruct_result24))
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
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t556 = _t555(msg)
        fields30 = _t556
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
        def _t557(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t558 = _t557(msg)
        fields35 = _t558
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
            _t559 = None
        else:
            _t559 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_boolean_value(self, msg: bool) -> Optional[Never]:
        def _t560(_dollar_dollar):
            return _dollar_dollar
        _t561 = _t560(msg)
        fields47 = _t561
        unwrapped_fields48 = fields47
        self.write('true')
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> Optional[Never]:
        def _t562(_dollar_dollar):
            return _dollar_dollar.fragments
        _t563 = _t562(msg)
        fields49 = _t563
        unwrapped_fields50 = fields49
        self.write('(')
        self.write('sync')
        self.newline()
        self.indent()
        for i52, elem51 in enumerate(unwrapped_fields50):
            
            if (i52 > 0):
                self.newline()
                _t564 = None
            else:
                _t564 = None
            _t565 = self.pretty_fragment_id(elem51)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t566(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t567 = _t566(msg)
        fields53 = _t567
        unwrapped_fields54 = fields53
        self.write(':')
        self.write(unwrapped_fields54)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> Optional[Never]:
        def _t568(_dollar_dollar):
            
            if not len(_dollar_dollar.writes) == 0:
                _t569 = _dollar_dollar.writes
            else:
                _t569 = None
            
            if not len(_dollar_dollar.reads) == 0:
                _t570 = _dollar_dollar.reads
            else:
                _t570 = None
            return (_t569, _t570,)
        _t571 = _t568(msg)
        fields55 = _t571
        unwrapped_fields56 = fields55
        self.write('(')
        self.write('epoch')
        self.newline()
        self.indent()
        field57 = unwrapped_fields56[0]
        
        if field57 is not None:
            opt_val58 = field57
            _t573 = self.pretty_epoch_writes(opt_val58)
            _t572 = _t573
        else:
            _t572 = None
        self.newline()
        field59 = unwrapped_fields56[1]
        
        if field59 is not None:
            opt_val60 = field59
            _t575 = self.pretty_epoch_reads(opt_val60)
            _t574 = _t575
        else:
            _t574 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_epoch_writes(self, msg: list[transactions_pb2.Write]) -> Optional[Never]:
        def _t576(_dollar_dollar):
            return _dollar_dollar
        _t577 = _t576(msg)
        fields61 = _t577
        unwrapped_fields62 = fields61
        self.write('(')
        self.write('writes')
        self.newline()
        self.indent()
        for i64, elem63 in enumerate(unwrapped_fields62):
            
            if (i64 > 0):
                self.newline()
                _t578 = None
            else:
                _t578 = None
            _t579 = self.pretty_write(elem63)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> Optional[Never]:
        def _t580(_dollar_dollar):
            
            if _dollar_dollar.HasField('define'):
                _t581 = _dollar_dollar.define
            else:
                _t581 = None
            return _t581
        _t582 = _t580(msg)
        deconstruct_result67 = _t582
        
        if deconstruct_result67 is not None:
            _t584 = self.pretty_define(deconstruct_result67)
            _t583 = _t584
        else:
            def _t585(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t586 = _dollar_dollar.undefine
                else:
                    _t586 = None
                return _t586
            _t587 = _t585(msg)
            deconstruct_result66 = _t587
            
            if deconstruct_result66 is not None:
                _t589 = self.pretty_undefine(deconstruct_result66)
                _t588 = _t589
            else:
                def _t590(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t591 = _dollar_dollar.context
                    else:
                        _t591 = None
                    return _t591
                _t592 = _t590(msg)
                deconstruct_result65 = _t592
                
                if deconstruct_result65 is not None:
                    _t594 = self.pretty_context(deconstruct_result65)
                    _t593 = _t594
                else:
                    raise ParseError('No matching rule for write')
                _t588 = _t593
            _t583 = _t588
        return _t583

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[Never]:
        def _t595(_dollar_dollar):
            return _dollar_dollar.fragment
        _t596 = _t595(msg)
        fields68 = _t596
        unwrapped_fields69 = fields68
        self.write('(')
        self.write('define')
        self.newline()
        self.indent()
        _t597 = self.pretty_fragment(unwrapped_fields69)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[Never]:
        def _t598(_dollar_dollar):
            _t599 = self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t600 = _t598(msg)
        fields70 = _t600
        unwrapped_fields71 = fields70
        self.write('(')
        self.write('fragment')
        self.newline()
        self.indent()
        field72 = unwrapped_fields71[0]
        _t601 = self.pretty_new_fragment_id(field72)
        self.newline()
        field73 = unwrapped_fields71[1]
        for i75, elem74 in enumerate(field73):
            
            if (i75 > 0):
                self.newline()
                _t602 = None
            else:
                _t602 = None
            _t603 = self.pretty_declaration(elem74)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t604(_dollar_dollar):
            return _dollar_dollar
        _t605 = _t604(msg)
        fields76 = _t605
        unwrapped_fields77 = fields76
        _t606 = self.pretty_fragment_id(unwrapped_fields77)
        return _t606

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[Never]:
        def _t607(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t608 = getattr(_dollar_dollar, 'def')
            else:
                _t608 = None
            return _t608
        _t609 = _t607(msg)
        deconstruct_result81 = _t609
        
        if deconstruct_result81 is not None:
            _t611 = self.pretty_def(deconstruct_result81)
            _t610 = _t611
        else:
            def _t612(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t613 = _dollar_dollar.algorithm
                else:
                    _t613 = None
                return _t613
            _t614 = _t612(msg)
            deconstruct_result80 = _t614
            
            if deconstruct_result80 is not None:
                _t616 = self.pretty_algorithm(deconstruct_result80)
                _t615 = _t616
            else:
                def _t617(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t618 = _dollar_dollar.constraint
                    else:
                        _t618 = None
                    return _t618
                _t619 = _t617(msg)
                deconstruct_result79 = _t619
                
                if deconstruct_result79 is not None:
                    _t621 = self.pretty_constraint(deconstruct_result79)
                    _t620 = _t621
                else:
                    def _t622(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('rel_edb'):
                            _t623 = _dollar_dollar.rel_edb
                        else:
                            _t623 = None
                        return _t623
                    _t624 = _t622(msg)
                    guard_result78 = _t624
                    
                    if guard_result78 is not None:
                        _t626 = self.pretty_data(msg)
                        _t625 = _t626
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t620 = _t625
                _t615 = _t620
            _t610 = _t615
        return _t610

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[Never]:
        def _t627(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t628 = _dollar_dollar.attrs
            else:
                _t628 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t628,)
        _t629 = _t627(msg)
        fields82 = _t629
        unwrapped_fields83 = fields82
        self.write('(')
        self.write('def')
        self.newline()
        self.indent()
        field84 = unwrapped_fields83[0]
        _t630 = self.pretty_relation_id(field84)
        self.newline()
        field85 = unwrapped_fields83[1]
        _t631 = self.pretty_abstraction(field85)
        self.newline()
        field86 = unwrapped_fields83[2]
        
        if field86 is not None:
            opt_val87 = field86
            _t633 = self.pretty_attrs(opt_val87)
            _t632 = _t633
        else:
            _t632 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[Never]:
        def _t634(_dollar_dollar):
            _t635 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t635
        _t636 = _t634(msg)
        deconstruct_result89 = _t636
        
        if deconstruct_result89 is not None:
            self.write(':')
            self.write(deconstruct_result89)
            _t637 = None
        else:
            def _t638(_dollar_dollar):
                _t639 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t639
            _t640 = _t638(msg)
            deconstruct_result88 = _t640
            
            if deconstruct_result88 is not None:
                self.write(self.format_uint128(deconstruct_result88))
                _t641 = None
            else:
                raise ParseError('No matching rule for relation_id')
            _t637 = _t641
        return _t637

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[Never]:
        def _t642(_dollar_dollar):
            _t643 = self.deconstruct_bindings(_dollar_dollar)
            return (_t643, _dollar_dollar.value,)
        _t644 = _t642(msg)
        fields90 = _t644
        unwrapped_fields91 = fields90
        self.write('(')
        field92 = unwrapped_fields91[0]
        _t645 = self.pretty_bindings(field92)
        field93 = unwrapped_fields91[1]
        _t646 = self.pretty_formula(field93)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_bindings(self, msg: tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]) -> Optional[Never]:
        def _t647(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t648 = _dollar_dollar[1]
            else:
                _t648 = None
            return (_dollar_dollar[0], _t648,)
        _t649 = _t647(msg)
        fields94 = _t649
        unwrapped_fields95 = fields94
        self.write('[')
        field96 = unwrapped_fields95[0]
        for i98, elem97 in enumerate(field96):
            
            if (i98 > 0):
                self.newline()
                _t650 = None
            else:
                _t650 = None
            _t651 = self.pretty_binding(elem97)
        field99 = unwrapped_fields95[1]
        
        if field99 is not None:
            opt_val100 = field99
            _t653 = self.pretty_value_bindings(opt_val100)
            _t652 = _t653
        else:
            _t652 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[Never]:
        def _t654(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t655 = _t654(msg)
        fields101 = _t655
        unwrapped_fields102 = fields101
        field103 = unwrapped_fields102[0]
        self.write(field103)
        self.write('::')
        field104 = unwrapped_fields102[1]
        _t656 = self.pretty_type(field104)
        return _t656

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[Never]:
        def _t657(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t658 = _dollar_dollar.unspecified_type
            else:
                _t658 = None
            return _t658
        _t659 = _t657(msg)
        deconstruct_result115 = _t659
        
        if deconstruct_result115 is not None:
            _t661 = self.pretty_unspecified_type(deconstruct_result115)
            _t660 = _t661
        else:
            def _t662(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t663 = _dollar_dollar.string_type
                else:
                    _t663 = None
                return _t663
            _t664 = _t662(msg)
            deconstruct_result114 = _t664
            
            if deconstruct_result114 is not None:
                _t666 = self.pretty_string_type(deconstruct_result114)
                _t665 = _t666
            else:
                def _t667(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t668 = _dollar_dollar.int_type
                    else:
                        _t668 = None
                    return _t668
                _t669 = _t667(msg)
                deconstruct_result113 = _t669
                
                if deconstruct_result113 is not None:
                    _t671 = self.pretty_int_type(deconstruct_result113)
                    _t670 = _t671
                else:
                    def _t672(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t673 = _dollar_dollar.float_type
                        else:
                            _t673 = None
                        return _t673
                    _t674 = _t672(msg)
                    deconstruct_result112 = _t674
                    
                    if deconstruct_result112 is not None:
                        _t676 = self.pretty_float_type(deconstruct_result112)
                        _t675 = _t676
                    else:
                        def _t677(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t678 = _dollar_dollar.uint128_type
                            else:
                                _t678 = None
                            return _t678
                        _t679 = _t677(msg)
                        deconstruct_result111 = _t679
                        
                        if deconstruct_result111 is not None:
                            _t681 = self.pretty_uint128_type(deconstruct_result111)
                            _t680 = _t681
                        else:
                            def _t682(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t683 = _dollar_dollar.int128_type
                                else:
                                    _t683 = None
                                return _t683
                            _t684 = _t682(msg)
                            deconstruct_result110 = _t684
                            
                            if deconstruct_result110 is not None:
                                _t686 = self.pretty_int128_type(deconstruct_result110)
                                _t685 = _t686
                            else:
                                def _t687(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t688 = _dollar_dollar.date_type
                                    else:
                                        _t688 = None
                                    return _t688
                                _t689 = _t687(msg)
                                deconstruct_result109 = _t689
                                
                                if deconstruct_result109 is not None:
                                    _t691 = self.pretty_date_type(deconstruct_result109)
                                    _t690 = _t691
                                else:
                                    def _t692(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t693 = _dollar_dollar.datetime_type
                                        else:
                                            _t693 = None
                                        return _t693
                                    _t694 = _t692(msg)
                                    deconstruct_result108 = _t694
                                    
                                    if deconstruct_result108 is not None:
                                        _t696 = self.pretty_datetime_type(deconstruct_result108)
                                        _t695 = _t696
                                    else:
                                        def _t697(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t698 = _dollar_dollar.missing_type
                                            else:
                                                _t698 = None
                                            return _t698
                                        _t699 = _t697(msg)
                                        deconstruct_result107 = _t699
                                        
                                        if deconstruct_result107 is not None:
                                            _t701 = self.pretty_missing_type(deconstruct_result107)
                                            _t700 = _t701
                                        else:
                                            def _t702(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t703 = _dollar_dollar.decimal_type
                                                else:
                                                    _t703 = None
                                                return _t703
                                            _t704 = _t702(msg)
                                            deconstruct_result106 = _t704
                                            
                                            if deconstruct_result106 is not None:
                                                _t706 = self.pretty_decimal_type(deconstruct_result106)
                                                _t705 = _t706
                                            else:
                                                def _t707(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t708 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t708 = None
                                                    return _t708
                                                _t709 = _t707(msg)
                                                deconstruct_result105 = _t709
                                                
                                                if deconstruct_result105 is not None:
                                                    _t711 = self.pretty_boolean_type(deconstruct_result105)
                                                    _t710 = _t711
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t705 = _t710
                                            _t700 = _t705
                                        _t695 = _t700
                                    _t690 = _t695
                                _t685 = _t690
                            _t680 = _t685
                        _t675 = _t680
                    _t670 = _t675
                _t665 = _t670
            _t660 = _t665
        return _t660

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[Never]:
        def _t712(_dollar_dollar):
            return _dollar_dollar
        _t713 = _t712(msg)
        fields116 = _t713
        unwrapped_fields117 = fields116
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[Never]:
        def _t714(_dollar_dollar):
            return _dollar_dollar
        _t715 = _t714(msg)
        fields118 = _t715
        unwrapped_fields119 = fields118
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[Never]:
        def _t716(_dollar_dollar):
            return _dollar_dollar
        _t717 = _t716(msg)
        fields120 = _t717
        unwrapped_fields121 = fields120
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[Never]:
        def _t718(_dollar_dollar):
            return _dollar_dollar
        _t719 = _t718(msg)
        fields122 = _t719
        unwrapped_fields123 = fields122
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[Never]:
        def _t720(_dollar_dollar):
            return _dollar_dollar
        _t721 = _t720(msg)
        fields124 = _t721
        unwrapped_fields125 = fields124
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[Never]:
        def _t722(_dollar_dollar):
            return _dollar_dollar
        _t723 = _t722(msg)
        fields126 = _t723
        unwrapped_fields127 = fields126
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[Never]:
        def _t724(_dollar_dollar):
            return _dollar_dollar
        _t725 = _t724(msg)
        fields128 = _t725
        unwrapped_fields129 = fields128
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[Never]:
        def _t726(_dollar_dollar):
            return _dollar_dollar
        _t727 = _t726(msg)
        fields130 = _t727
        unwrapped_fields131 = fields130
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[Never]:
        def _t728(_dollar_dollar):
            return _dollar_dollar
        _t729 = _t728(msg)
        fields132 = _t729
        unwrapped_fields133 = fields132
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[Never]:
        def _t730(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t731 = _t730(msg)
        fields134 = _t731
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
        def _t732(_dollar_dollar):
            return _dollar_dollar
        _t733 = _t732(msg)
        fields138 = _t733
        unwrapped_fields139 = fields138
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: list[logic_pb2.Binding]) -> Optional[Never]:
        def _t734(_dollar_dollar):
            return _dollar_dollar
        _t735 = _t734(msg)
        fields140 = _t735
        unwrapped_fields141 = fields140
        self.write('|')
        for i143, elem142 in enumerate(unwrapped_fields141):
            
            if (i143 > 0):
                self.newline()
                _t736 = None
            else:
                _t736 = None
            _t737 = self.pretty_binding(elem142)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[Never]:
        def _t738(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t739 = _dollar_dollar.conjunction
            else:
                _t739 = None
            return _t739
        _t740 = _t738(msg)
        deconstruct_result156 = _t740
        
        if deconstruct_result156 is not None:
            _t742 = self.pretty_true(deconstruct_result156)
            _t741 = _t742
        else:
            def _t743(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t744 = _dollar_dollar.disjunction
                else:
                    _t744 = None
                return _t744
            _t745 = _t743(msg)
            deconstruct_result155 = _t745
            
            if deconstruct_result155 is not None:
                _t747 = self.pretty_false(deconstruct_result155)
                _t746 = _t747
            else:
                def _t748(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t749 = _dollar_dollar.exists
                    else:
                        _t749 = None
                    return _t749
                _t750 = _t748(msg)
                deconstruct_result154 = _t750
                
                if deconstruct_result154 is not None:
                    _t752 = self.pretty_exists(deconstruct_result154)
                    _t751 = _t752
                else:
                    def _t753(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t754 = _dollar_dollar.reduce
                        else:
                            _t754 = None
                        return _t754
                    _t755 = _t753(msg)
                    deconstruct_result153 = _t755
                    
                    if deconstruct_result153 is not None:
                        _t757 = self.pretty_reduce(deconstruct_result153)
                        _t756 = _t757
                    else:
                        def _t758(_dollar_dollar):
                            
                            if (_dollar_dollar.HasField('conjunction') and not len(_dollar_dollar.conjunction.args) == 0):
                                _t759 = _dollar_dollar.conjunction
                            else:
                                _t759 = None
                            return _t759
                        _t760 = _t758(msg)
                        deconstruct_result152 = _t760
                        
                        if deconstruct_result152 is not None:
                            _t762 = self.pretty_conjunction(deconstruct_result152)
                            _t761 = _t762
                        else:
                            def _t763(_dollar_dollar):
                                
                                if (_dollar_dollar.HasField('disjunction') and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t764 = _dollar_dollar.disjunction
                                else:
                                    _t764 = None
                                return _t764
                            _t765 = _t763(msg)
                            deconstruct_result151 = _t765
                            
                            if deconstruct_result151 is not None:
                                _t767 = self.pretty_disjunction(deconstruct_result151)
                                _t766 = _t767
                            else:
                                def _t768(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t769 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t769 = None
                                    return _t769
                                _t770 = _t768(msg)
                                deconstruct_result150 = _t770
                                
                                if deconstruct_result150 is not None:
                                    _t772 = self.pretty_not(deconstruct_result150)
                                    _t771 = _t772
                                else:
                                    def _t773(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t774 = _dollar_dollar.ffi
                                        else:
                                            _t774 = None
                                        return _t774
                                    _t775 = _t773(msg)
                                    deconstruct_result149 = _t775
                                    
                                    if deconstruct_result149 is not None:
                                        _t777 = self.pretty_ffi(deconstruct_result149)
                                        _t776 = _t777
                                    else:
                                        def _t778(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t779 = _dollar_dollar.atom
                                            else:
                                                _t779 = None
                                            return _t779
                                        _t780 = _t778(msg)
                                        deconstruct_result148 = _t780
                                        
                                        if deconstruct_result148 is not None:
                                            _t782 = self.pretty_atom(deconstruct_result148)
                                            _t781 = _t782
                                        else:
                                            def _t783(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t784 = _dollar_dollar.pragma
                                                else:
                                                    _t784 = None
                                                return _t784
                                            _t785 = _t783(msg)
                                            deconstruct_result147 = _t785
                                            
                                            if deconstruct_result147 is not None:
                                                _t787 = self.pretty_pragma(deconstruct_result147)
                                                _t786 = _t787
                                            else:
                                                def _t788(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t789 = _dollar_dollar.primitive
                                                    else:
                                                        _t789 = None
                                                    return _t789
                                                _t790 = _t788(msg)
                                                deconstruct_result146 = _t790
                                                
                                                if deconstruct_result146 is not None:
                                                    _t792 = self.pretty_primitive(deconstruct_result146)
                                                    _t791 = _t792
                                                else:
                                                    def _t793(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t794 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t794 = None
                                                        return _t794
                                                    _t795 = _t793(msg)
                                                    deconstruct_result145 = _t795
                                                    
                                                    if deconstruct_result145 is not None:
                                                        _t797 = self.pretty_rel_atom(deconstruct_result145)
                                                        _t796 = _t797
                                                    else:
                                                        def _t798(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t799 = _dollar_dollar.cast
                                                            else:
                                                                _t799 = None
                                                            return _t799
                                                        _t800 = _t798(msg)
                                                        deconstruct_result144 = _t800
                                                        
                                                        if deconstruct_result144 is not None:
                                                            _t802 = self.pretty_cast(deconstruct_result144)
                                                            _t801 = _t802
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t796 = _t801
                                                    _t791 = _t796
                                                _t786 = _t791
                                            _t781 = _t786
                                        _t776 = _t781
                                    _t771 = _t776
                                _t766 = _t771
                            _t761 = _t766
                        _t756 = _t761
                    _t751 = _t756
                _t746 = _t751
            _t741 = _t746
        return _t741

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t803(_dollar_dollar):
            return _dollar_dollar
        _t804 = _t803(msg)
        fields157 = _t804
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
        def _t805(_dollar_dollar):
            return _dollar_dollar
        _t806 = _t805(msg)
        fields159 = _t806
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
        def _t807(_dollar_dollar):
            _t808 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t808, _dollar_dollar.body.value,)
        _t809 = _t807(msg)
        fields161 = _t809
        unwrapped_fields162 = fields161
        self.write('(')
        self.write('exists')
        self.newline()
        self.indent()
        field163 = unwrapped_fields162[0]
        _t810 = self.pretty_bindings(field163)
        self.newline()
        field164 = unwrapped_fields162[1]
        _t811 = self.pretty_formula(field164)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[Never]:
        def _t812(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t813 = _t812(msg)
        fields165 = _t813
        unwrapped_fields166 = fields165
        self.write('(')
        self.write('reduce')
        self.newline()
        self.indent()
        field167 = unwrapped_fields166[0]
        _t814 = self.pretty_abstraction(field167)
        self.newline()
        field168 = unwrapped_fields166[1]
        _t815 = self.pretty_abstraction(field168)
        self.newline()
        field169 = unwrapped_fields166[2]
        _t816 = self.pretty_terms(field169)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_terms(self, msg: list[logic_pb2.Term]) -> Optional[Never]:
        def _t817(_dollar_dollar):
            return _dollar_dollar
        _t818 = _t817(msg)
        fields170 = _t818
        unwrapped_fields171 = fields170
        self.write('(')
        self.write('terms')
        self.newline()
        self.indent()
        for i173, elem172 in enumerate(unwrapped_fields171):
            
            if (i173 > 0):
                self.newline()
                _t819 = None
            else:
                _t819 = None
            _t820 = self.pretty_term(elem172)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[Never]:
        def _t821(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t822 = _dollar_dollar.var
            else:
                _t822 = None
            return _t822
        _t823 = _t821(msg)
        deconstruct_result175 = _t823
        
        if deconstruct_result175 is not None:
            _t825 = self.pretty_var(deconstruct_result175)
            _t824 = _t825
        else:
            def _t826(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t827 = _dollar_dollar.constant
                else:
                    _t827 = None
                return _t827
            _t828 = _t826(msg)
            deconstruct_result174 = _t828
            
            if deconstruct_result174 is not None:
                _t830 = self.pretty_constant(deconstruct_result174)
                _t829 = _t830
            else:
                raise ParseError('No matching rule for term')
            _t824 = _t829
        return _t824

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[Never]:
        def _t831(_dollar_dollar):
            return _dollar_dollar.name
        _t832 = _t831(msg)
        fields176 = _t832
        unwrapped_fields177 = fields176
        self.write(unwrapped_fields177)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t833(_dollar_dollar):
            return _dollar_dollar
        _t834 = _t833(msg)
        fields178 = _t834
        unwrapped_fields179 = fields178
        _t835 = self.pretty_value(unwrapped_fields179)
        return _t835

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t836(_dollar_dollar):
            return _dollar_dollar.args
        _t837 = _t836(msg)
        fields180 = _t837
        unwrapped_fields181 = fields180
        self.write('(')
        self.write('and')
        self.newline()
        self.indent()
        for i183, elem182 in enumerate(unwrapped_fields181):
            
            if (i183 > 0):
                self.newline()
                _t838 = None
            else:
                _t838 = None
            _t839 = self.pretty_formula(elem182)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t840(_dollar_dollar):
            return _dollar_dollar.args
        _t841 = _t840(msg)
        fields184 = _t841
        unwrapped_fields185 = fields184
        self.write('(')
        self.write('or')
        self.newline()
        self.indent()
        for i187, elem186 in enumerate(unwrapped_fields185):
            
            if (i187 > 0):
                self.newline()
                _t842 = None
            else:
                _t842 = None
            _t843 = self.pretty_formula(elem186)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[Never]:
        def _t844(_dollar_dollar):
            return _dollar_dollar.arg
        _t845 = _t844(msg)
        fields188 = _t845
        unwrapped_fields189 = fields188
        self.write('(')
        self.write('not')
        self.newline()
        self.indent()
        _t846 = self.pretty_formula(unwrapped_fields189)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[Never]:
        def _t847(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t848 = _t847(msg)
        fields190 = _t848
        unwrapped_fields191 = fields190
        self.write('(')
        self.write('ffi')
        self.newline()
        self.indent()
        field192 = unwrapped_fields191[0]
        _t849 = self.pretty_name(field192)
        self.newline()
        field193 = unwrapped_fields191[1]
        _t850 = self.pretty_ffi_args(field193)
        self.newline()
        field194 = unwrapped_fields191[2]
        _t851 = self.pretty_terms(field194)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_name(self, msg: str) -> Optional[Never]:
        def _t852(_dollar_dollar):
            return _dollar_dollar
        _t853 = _t852(msg)
        fields195 = _t853
        unwrapped_fields196 = fields195
        self.write(':')
        self.write(unwrapped_fields196)
        return None

    def pretty_ffi_args(self, msg: list[logic_pb2.Abstraction]) -> Optional[Never]:
        def _t854(_dollar_dollar):
            return _dollar_dollar
        _t855 = _t854(msg)
        fields197 = _t855
        unwrapped_fields198 = fields197
        self.write('(')
        self.write('args')
        self.newline()
        self.indent()
        for i200, elem199 in enumerate(unwrapped_fields198):
            
            if (i200 > 0):
                self.newline()
                _t856 = None
            else:
                _t856 = None
            _t857 = self.pretty_abstraction(elem199)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[Never]:
        def _t858(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t859 = _t858(msg)
        fields201 = _t859
        unwrapped_fields202 = fields201
        self.write('(')
        self.write('atom')
        self.newline()
        self.indent()
        field203 = unwrapped_fields202[0]
        _t860 = self.pretty_relation_id(field203)
        self.newline()
        field204 = unwrapped_fields202[1]
        for i206, elem205 in enumerate(field204):
            
            if (i206 > 0):
                self.newline()
                _t861 = None
            else:
                _t861 = None
            _t862 = self.pretty_term(elem205)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[Never]:
        def _t863(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t864 = _t863(msg)
        fields207 = _t864
        unwrapped_fields208 = fields207
        self.write('(')
        self.write('pragma')
        self.newline()
        self.indent()
        field209 = unwrapped_fields208[0]
        _t865 = self.pretty_name(field209)
        self.newline()
        field210 = unwrapped_fields208[1]
        for i212, elem211 in enumerate(field210):
            
            if (i212 > 0):
                self.newline()
                _t866 = None
            else:
                _t866 = None
            _t867 = self.pretty_term(elem211)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t868(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t869 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t869 = None
            return _t869
        _t870 = _t868(msg)
        guard_result227 = _t870
        
        if guard_result227 is not None:
            _t872 = self.pretty_eq(msg)
            _t871 = _t872
        else:
            def _t873(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t874 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t874 = None
                return _t874
            _t875 = _t873(msg)
            guard_result226 = _t875
            
            if guard_result226 is not None:
                _t877 = self.pretty_lt(msg)
                _t876 = _t877
            else:
                def _t878(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t879 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t879 = None
                    return _t879
                _t880 = _t878(msg)
                guard_result225 = _t880
                
                if guard_result225 is not None:
                    _t882 = self.pretty_lt_eq(msg)
                    _t881 = _t882
                else:
                    def _t883(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t884 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t884 = None
                        return _t884
                    _t885 = _t883(msg)
                    guard_result224 = _t885
                    
                    if guard_result224 is not None:
                        _t887 = self.pretty_gt(msg)
                        _t886 = _t887
                    else:
                        def _t888(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t889 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t889 = None
                            return _t889
                        _t890 = _t888(msg)
                        guard_result223 = _t890
                        
                        if guard_result223 is not None:
                            _t892 = self.pretty_gt_eq(msg)
                            _t891 = _t892
                        else:
                            def _t893(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t894 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t894 = None
                                return _t894
                            _t895 = _t893(msg)
                            guard_result222 = _t895
                            
                            if guard_result222 is not None:
                                _t897 = self.pretty_add(msg)
                                _t896 = _t897
                            else:
                                def _t898(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t899 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t899 = None
                                    return _t899
                                _t900 = _t898(msg)
                                guard_result221 = _t900
                                
                                if guard_result221 is not None:
                                    _t902 = self.pretty_minus(msg)
                                    _t901 = _t902
                                else:
                                    def _t903(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t904 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t904 = None
                                        return _t904
                                    _t905 = _t903(msg)
                                    guard_result220 = _t905
                                    
                                    if guard_result220 is not None:
                                        _t907 = self.pretty_multiply(msg)
                                        _t906 = _t907
                                    else:
                                        def _t908(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t909 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t909 = None
                                            return _t909
                                        _t910 = _t908(msg)
                                        guard_result219 = _t910
                                        
                                        if guard_result219 is not None:
                                            _t912 = self.pretty_divide(msg)
                                            _t911 = _t912
                                        else:
                                            def _t913(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t914 = _t913(msg)
                                            fields213 = _t914
                                            unwrapped_fields214 = fields213
                                            self.write('(')
                                            self.write('primitive')
                                            self.newline()
                                            self.indent()
                                            field215 = unwrapped_fields214[0]
                                            _t915 = self.pretty_name(field215)
                                            self.newline()
                                            field216 = unwrapped_fields214[1]
                                            for i218, elem217 in enumerate(field216):
                                                
                                                if (i218 > 0):
                                                    self.newline()
                                                    _t916 = None
                                                else:
                                                    _t916 = None
                                                _t917 = self.pretty_rel_term(elem217)
                                            self.dedent()
                                            self.write(')')
                                            self.newline()
                                            _t911 = None
                                        _t906 = _t911
                                    _t901 = _t906
                                _t896 = _t901
                            _t891 = _t896
                        _t886 = _t891
                    _t881 = _t886
                _t876 = _t881
            _t871 = _t876
        return _t871

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t918(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t919 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t919 = None
            return _t919
        _t920 = _t918(msg)
        fields228 = _t920
        unwrapped_fields229 = fields228
        self.write('(')
        self.write('=')
        self.newline()
        self.indent()
        field230 = unwrapped_fields229[0]
        _t921 = self.pretty_term(field230)
        self.newline()
        field231 = unwrapped_fields229[1]
        _t922 = self.pretty_term(field231)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t923(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t924 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t924 = None
            return _t924
        _t925 = _t923(msg)
        fields232 = _t925
        unwrapped_fields233 = fields232
        self.write('(')
        self.write('<')
        self.newline()
        self.indent()
        field234 = unwrapped_fields233[0]
        _t926 = self.pretty_term(field234)
        self.newline()
        field235 = unwrapped_fields233[1]
        _t927 = self.pretty_term(field235)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t928(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t929 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t929 = None
            return _t929
        _t930 = _t928(msg)
        fields236 = _t930
        unwrapped_fields237 = fields236
        self.write('(')
        self.write('<=')
        self.newline()
        self.indent()
        field238 = unwrapped_fields237[0]
        _t931 = self.pretty_term(field238)
        self.newline()
        field239 = unwrapped_fields237[1]
        _t932 = self.pretty_term(field239)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t933(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t934 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t934 = None
            return _t934
        _t935 = _t933(msg)
        fields240 = _t935
        unwrapped_fields241 = fields240
        self.write('(')
        self.write('>')
        self.newline()
        self.indent()
        field242 = unwrapped_fields241[0]
        _t936 = self.pretty_term(field242)
        self.newline()
        field243 = unwrapped_fields241[1]
        _t937 = self.pretty_term(field243)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t938(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t939 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t939 = None
            return _t939
        _t940 = _t938(msg)
        fields244 = _t940
        unwrapped_fields245 = fields244
        self.write('(')
        self.write('>=')
        self.newline()
        self.indent()
        field246 = unwrapped_fields245[0]
        _t941 = self.pretty_term(field246)
        self.newline()
        field247 = unwrapped_fields245[1]
        _t942 = self.pretty_term(field247)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t943(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t944 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t944 = None
            return _t944
        _t945 = _t943(msg)
        fields248 = _t945
        unwrapped_fields249 = fields248
        self.write('(')
        self.write('+')
        self.newline()
        self.indent()
        field250 = unwrapped_fields249[0]
        _t946 = self.pretty_term(field250)
        self.newline()
        field251 = unwrapped_fields249[1]
        _t947 = self.pretty_term(field251)
        self.newline()
        field252 = unwrapped_fields249[2]
        _t948 = self.pretty_term(field252)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t949(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t950 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t950 = None
            return _t950
        _t951 = _t949(msg)
        fields253 = _t951
        unwrapped_fields254 = fields253
        self.write('(')
        self.write('-')
        self.newline()
        self.indent()
        field255 = unwrapped_fields254[0]
        _t952 = self.pretty_term(field255)
        self.newline()
        field256 = unwrapped_fields254[1]
        _t953 = self.pretty_term(field256)
        self.newline()
        field257 = unwrapped_fields254[2]
        _t954 = self.pretty_term(field257)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t955(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t956 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t956 = None
            return _t956
        _t957 = _t955(msg)
        fields258 = _t957
        unwrapped_fields259 = fields258
        self.write('(')
        self.write('*')
        self.newline()
        self.indent()
        field260 = unwrapped_fields259[0]
        _t958 = self.pretty_term(field260)
        self.newline()
        field261 = unwrapped_fields259[1]
        _t959 = self.pretty_term(field261)
        self.newline()
        field262 = unwrapped_fields259[2]
        _t960 = self.pretty_term(field262)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t961(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t962 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t962 = None
            return _t962
        _t963 = _t961(msg)
        fields263 = _t963
        unwrapped_fields264 = fields263
        self.write('(')
        self.write('/')
        self.newline()
        self.indent()
        field265 = unwrapped_fields264[0]
        _t964 = self.pretty_term(field265)
        self.newline()
        field266 = unwrapped_fields264[1]
        _t965 = self.pretty_term(field266)
        self.newline()
        field267 = unwrapped_fields264[2]
        _t966 = self.pretty_term(field267)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[Never]:
        def _t967(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t968 = _dollar_dollar.specialized_value
            else:
                _t968 = None
            return _t968
        _t969 = _t967(msg)
        deconstruct_result269 = _t969
        
        if deconstruct_result269 is not None:
            _t971 = self.pretty_specialized_value(deconstruct_result269)
            _t970 = _t971
        else:
            def _t972(_dollar_dollar):
                
                if _dollar_dollar.HasField('var'):
                    _t973 = _dollar_dollar.var
                else:
                    _t973 = None
                return _t973
            _t974 = _t972(msg)
            guard_result268 = _t974
            
            if guard_result268 is not None:
                _t976 = self.pretty_term(msg)
                _t975 = _t976
            else:
                raise ParseError('No matching rule for rel_term')
            _t970 = _t975
        return _t970

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t977(_dollar_dollar):
            return _dollar_dollar
        _t978 = _t977(msg)
        fields270 = _t978
        unwrapped_fields271 = fields270
        self.write('#')
        _t979 = self.pretty_value(unwrapped_fields271)
        return _t979

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[Never]:
        def _t980(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t981 = _t980(msg)
        fields272 = _t981
        unwrapped_fields273 = fields272
        self.write('(')
        self.write('relatom')
        self.newline()
        self.indent()
        field274 = unwrapped_fields273[0]
        _t982 = self.pretty_name(field274)
        self.newline()
        field275 = unwrapped_fields273[1]
        for i277, elem276 in enumerate(field275):
            
            if (i277 > 0):
                self.newline()
                _t983 = None
            else:
                _t983 = None
            _t984 = self.pretty_rel_term(elem276)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[Never]:
        def _t985(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t986 = _t985(msg)
        fields278 = _t986
        unwrapped_fields279 = fields278
        self.write('(')
        self.write('cast')
        self.newline()
        self.indent()
        field280 = unwrapped_fields279[0]
        _t987 = self.pretty_term(field280)
        self.newline()
        field281 = unwrapped_fields279[1]
        _t988 = self.pretty_term(field281)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_attrs(self, msg: list[logic_pb2.Attribute]) -> Optional[Never]:
        def _t989(_dollar_dollar):
            return _dollar_dollar
        _t990 = _t989(msg)
        fields282 = _t990
        unwrapped_fields283 = fields282
        self.write('(')
        self.write('attrs')
        self.newline()
        self.indent()
        for i285, elem284 in enumerate(unwrapped_fields283):
            
            if (i285 > 0):
                self.newline()
                _t991 = None
            else:
                _t991 = None
            _t992 = self.pretty_attribute(elem284)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[Never]:
        def _t993(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t994 = _t993(msg)
        fields286 = _t994
        unwrapped_fields287 = fields286
        self.write('(')
        self.write('attribute')
        self.newline()
        self.indent()
        field288 = unwrapped_fields287[0]
        _t995 = self.pretty_name(field288)
        self.newline()
        field289 = unwrapped_fields287[1]
        for i291, elem290 in enumerate(field289):
            
            if (i291 > 0):
                self.newline()
                _t996 = None
            else:
                _t996 = None
            _t997 = self.pretty_value(elem290)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[Never]:
        def _t998(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t999 = _t998(msg)
        fields292 = _t999
        unwrapped_fields293 = fields292
        self.write('(')
        self.write('algorithm')
        self.newline()
        self.indent()
        field294 = unwrapped_fields293[0]
        for i296, elem295 in enumerate(field294):
            
            if (i296 > 0):
                self.newline()
                _t1000 = None
            else:
                _t1000 = None
            _t1001 = self.pretty_relation_id(elem295)
        self.newline()
        field297 = unwrapped_fields293[1]
        _t1002 = self.pretty_script(field297)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[Never]:
        def _t1003(_dollar_dollar):
            return _dollar_dollar.constructs
        _t1004 = _t1003(msg)
        fields298 = _t1004
        unwrapped_fields299 = fields298
        self.write('(')
        self.write('script')
        self.newline()
        self.indent()
        for i301, elem300 in enumerate(unwrapped_fields299):
            
            if (i301 > 0):
                self.newline()
                _t1005 = None
            else:
                _t1005 = None
            _t1006 = self.pretty_construct(elem300)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[Never]:
        def _t1007(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t1008 = _dollar_dollar.loop
            else:
                _t1008 = None
            return _t1008
        _t1009 = _t1007(msg)
        deconstruct_result303 = _t1009
        
        if deconstruct_result303 is not None:
            _t1011 = self.pretty_loop(deconstruct_result303)
            _t1010 = _t1011
        else:
            def _t1012(_dollar_dollar):
                
                if _dollar_dollar.HasField('assign'):
                    _t1013 = _dollar_dollar.assign
                else:
                    _t1013 = None
                return _t1013
            _t1014 = _t1012(msg)
            guard_result302 = _t1014
            
            if guard_result302 is not None:
                _t1016 = self.pretty_instruction(msg)
                _t1015 = _t1016
            else:
                raise ParseError('No matching rule for construct')
            _t1010 = _t1015
        return _t1010

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[Never]:
        def _t1017(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1018 = _t1017(msg)
        fields304 = _t1018
        unwrapped_fields305 = fields304
        self.write('(')
        self.write('loop')
        self.newline()
        self.indent()
        field306 = unwrapped_fields305[0]
        _t1019 = self.pretty_init(field306)
        self.newline()
        field307 = unwrapped_fields305[1]
        _t1020 = self.pretty_script(field307)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_init(self, msg: list[logic_pb2.Instruction]) -> Optional[Never]:
        def _t1021(_dollar_dollar):
            return _dollar_dollar
        _t1022 = _t1021(msg)
        fields308 = _t1022
        unwrapped_fields309 = fields308
        self.write('(')
        self.write('init')
        self.newline()
        self.indent()
        for i311, elem310 in enumerate(unwrapped_fields309):
            
            if (i311 > 0):
                self.newline()
                _t1023 = None
            else:
                _t1023 = None
            _t1024 = self.pretty_instruction(elem310)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[Never]:
        def _t1025(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1026 = _dollar_dollar.assign
            else:
                _t1026 = None
            return _t1026
        _t1027 = _t1025(msg)
        deconstruct_result316 = _t1027
        
        if deconstruct_result316 is not None:
            _t1029 = self.pretty_assign(deconstruct_result316)
            _t1028 = _t1029
        else:
            def _t1030(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1031 = _dollar_dollar.upsert
                else:
                    _t1031 = None
                return _t1031
            _t1032 = _t1030(msg)
            deconstruct_result315 = _t1032
            
            if deconstruct_result315 is not None:
                _t1034 = self.pretty_upsert(deconstruct_result315)
                _t1033 = _t1034
            else:
                def _t1035(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1036 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1036 = None
                    return _t1036
                _t1037 = _t1035(msg)
                deconstruct_result314 = _t1037
                
                if deconstruct_result314 is not None:
                    _t1039 = self.pretty_break(deconstruct_result314)
                    _t1038 = _t1039
                else:
                    def _t1040(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1041 = _dollar_dollar.monoid_def
                        else:
                            _t1041 = None
                        return _t1041
                    _t1042 = _t1040(msg)
                    deconstruct_result313 = _t1042
                    
                    if deconstruct_result313 is not None:
                        _t1044 = self.pretty_monoid_def(deconstruct_result313)
                        _t1043 = _t1044
                    else:
                        def _t1045(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1046 = _dollar_dollar.monus_def
                            else:
                                _t1046 = None
                            return _t1046
                        _t1047 = _t1045(msg)
                        deconstruct_result312 = _t1047
                        
                        if deconstruct_result312 is not None:
                            _t1049 = self.pretty_monus_def(deconstruct_result312)
                            _t1048 = _t1049
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1043 = _t1048
                    _t1038 = _t1043
                _t1033 = _t1038
            _t1028 = _t1033
        return _t1028

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[Never]:
        def _t1050(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1051 = _dollar_dollar.attrs
            else:
                _t1051 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1051,)
        _t1052 = _t1050(msg)
        fields317 = _t1052
        unwrapped_fields318 = fields317
        self.write('(')
        self.write('assign')
        self.newline()
        self.indent()
        field319 = unwrapped_fields318[0]
        _t1053 = self.pretty_relation_id(field319)
        self.newline()
        field320 = unwrapped_fields318[1]
        _t1054 = self.pretty_abstraction(field320)
        self.newline()
        field321 = unwrapped_fields318[2]
        
        if field321 is not None:
            opt_val322 = field321
            _t1056 = self.pretty_attrs(opt_val322)
            _t1055 = _t1056
        else:
            _t1055 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[Never]:
        def _t1057(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1058 = _dollar_dollar.attrs
            else:
                _t1058 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1058,)
        _t1059 = _t1057(msg)
        fields323 = _t1059
        unwrapped_fields324 = fields323
        self.write('(')
        self.write('upsert')
        self.newline()
        self.indent()
        field325 = unwrapped_fields324[0]
        _t1060 = self.pretty_relation_id(field325)
        self.newline()
        field326 = unwrapped_fields324[1]
        _t1061 = self.pretty_abstraction_with_arity(field326)
        self.newline()
        field327 = unwrapped_fields324[2]
        
        if field327 is not None:
            opt_val328 = field327
            _t1063 = self.pretty_attrs(opt_val328)
            _t1062 = _t1063
        else:
            _t1062 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[Never]:
        def _t1064(_dollar_dollar):
            _t1065 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1065, _dollar_dollar[0].value,)
        _t1066 = _t1064(msg)
        fields329 = _t1066
        unwrapped_fields330 = fields329
        self.write('(')
        field331 = unwrapped_fields330[0]
        _t1067 = self.pretty_bindings(field331)
        field332 = unwrapped_fields330[1]
        _t1068 = self.pretty_formula(field332)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[Never]:
        def _t1069(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1070 = _dollar_dollar.attrs
            else:
                _t1070 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1070,)
        _t1071 = _t1069(msg)
        fields333 = _t1071
        unwrapped_fields334 = fields333
        self.write('(')
        self.write('break')
        self.newline()
        self.indent()
        field335 = unwrapped_fields334[0]
        _t1072 = self.pretty_relation_id(field335)
        self.newline()
        field336 = unwrapped_fields334[1]
        _t1073 = self.pretty_abstraction(field336)
        self.newline()
        field337 = unwrapped_fields334[2]
        
        if field337 is not None:
            opt_val338 = field337
            _t1075 = self.pretty_attrs(opt_val338)
            _t1074 = _t1075
        else:
            _t1074 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[Never]:
        def _t1076(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1077 = _dollar_dollar.attrs
            else:
                _t1077 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1077,)
        _t1078 = _t1076(msg)
        fields339 = _t1078
        unwrapped_fields340 = fields339
        self.write('(')
        self.write('monoid')
        self.newline()
        self.indent()
        field341 = unwrapped_fields340[0]
        _t1079 = self.pretty_monoid(field341)
        self.newline()
        field342 = unwrapped_fields340[1]
        _t1080 = self.pretty_relation_id(field342)
        self.newline()
        field343 = unwrapped_fields340[2]
        _t1081 = self.pretty_abstraction_with_arity(field343)
        self.newline()
        field344 = unwrapped_fields340[3]
        
        if field344 is not None:
            opt_val345 = field344
            _t1083 = self.pretty_attrs(opt_val345)
            _t1082 = _t1083
        else:
            _t1082 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[Never]:
        def _t1084(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1085 = _dollar_dollar.or_monoid
            else:
                _t1085 = None
            return _t1085
        _t1086 = _t1084(msg)
        deconstruct_result349 = _t1086
        
        if deconstruct_result349 is not None:
            _t1088 = self.pretty_or_monoid(deconstruct_result349)
            _t1087 = _t1088
        else:
            def _t1089(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1090 = _dollar_dollar.min_monoid
                else:
                    _t1090 = None
                return _t1090
            _t1091 = _t1089(msg)
            deconstruct_result348 = _t1091
            
            if deconstruct_result348 is not None:
                _t1093 = self.pretty_min_monoid(deconstruct_result348)
                _t1092 = _t1093
            else:
                def _t1094(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1095 = _dollar_dollar.max_monoid
                    else:
                        _t1095 = None
                    return _t1095
                _t1096 = _t1094(msg)
                deconstruct_result347 = _t1096
                
                if deconstruct_result347 is not None:
                    _t1098 = self.pretty_max_monoid(deconstruct_result347)
                    _t1097 = _t1098
                else:
                    def _t1099(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1100 = _dollar_dollar.sum_monoid
                        else:
                            _t1100 = None
                        return _t1100
                    _t1101 = _t1099(msg)
                    deconstruct_result346 = _t1101
                    
                    if deconstruct_result346 is not None:
                        _t1103 = self.pretty_sum_monoid(deconstruct_result346)
                        _t1102 = _t1103
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1097 = _t1102
                _t1092 = _t1097
            _t1087 = _t1092
        return _t1087

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[Never]:
        def _t1104(_dollar_dollar):
            return _dollar_dollar
        _t1105 = _t1104(msg)
        fields350 = _t1105
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
        def _t1106(_dollar_dollar):
            return _dollar_dollar.type
        _t1107 = _t1106(msg)
        fields352 = _t1107
        unwrapped_fields353 = fields352
        self.write('(')
        self.write('min')
        self.newline()
        self.indent()
        _t1108 = self.pretty_type(unwrapped_fields353)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[Never]:
        def _t1109(_dollar_dollar):
            return _dollar_dollar.type
        _t1110 = _t1109(msg)
        fields354 = _t1110
        unwrapped_fields355 = fields354
        self.write('(')
        self.write('max')
        self.newline()
        self.indent()
        _t1111 = self.pretty_type(unwrapped_fields355)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[Never]:
        def _t1112(_dollar_dollar):
            return _dollar_dollar.type
        _t1113 = _t1112(msg)
        fields356 = _t1113
        unwrapped_fields357 = fields356
        self.write('(')
        self.write('sum')
        self.newline()
        self.indent()
        _t1114 = self.pretty_type(unwrapped_fields357)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[Never]:
        def _t1115(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1116 = _dollar_dollar.attrs
            else:
                _t1116 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1116,)
        _t1117 = _t1115(msg)
        fields358 = _t1117
        unwrapped_fields359 = fields358
        self.write('(')
        self.write('monus')
        self.newline()
        self.indent()
        field360 = unwrapped_fields359[0]
        _t1118 = self.pretty_monoid(field360)
        self.newline()
        field361 = unwrapped_fields359[1]
        _t1119 = self.pretty_relation_id(field361)
        self.newline()
        field362 = unwrapped_fields359[2]
        _t1120 = self.pretty_abstraction_with_arity(field362)
        self.newline()
        field363 = unwrapped_fields359[3]
        
        if field363 is not None:
            opt_val364 = field363
            _t1122 = self.pretty_attrs(opt_val364)
            _t1121 = _t1122
        else:
            _t1121 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[Never]:
        def _t1123(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1124 = _t1123(msg)
        fields365 = _t1124
        unwrapped_fields366 = fields365
        self.write('(')
        self.write('functional_dependency')
        self.newline()
        self.indent()
        field367 = unwrapped_fields366[0]
        _t1125 = self.pretty_relation_id(field367)
        self.newline()
        field368 = unwrapped_fields366[1]
        _t1126 = self.pretty_abstraction(field368)
        self.newline()
        field369 = unwrapped_fields366[2]
        _t1127 = self.pretty_functional_dependency_keys(field369)
        self.newline()
        field370 = unwrapped_fields366[3]
        _t1128 = self.pretty_functional_dependency_values(field370)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_functional_dependency_keys(self, msg: list[logic_pb2.Var]) -> Optional[Never]:
        def _t1129(_dollar_dollar):
            return _dollar_dollar
        _t1130 = _t1129(msg)
        fields371 = _t1130
        unwrapped_fields372 = fields371
        self.write('(')
        self.write('keys')
        self.newline()
        self.indent()
        for i374, elem373 in enumerate(unwrapped_fields372):
            
            if (i374 > 0):
                self.newline()
                _t1131 = None
            else:
                _t1131 = None
            _t1132 = self.pretty_var(elem373)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_functional_dependency_values(self, msg: list[logic_pb2.Var]) -> Optional[Never]:
        def _t1133(_dollar_dollar):
            return _dollar_dollar
        _t1134 = _t1133(msg)
        fields375 = _t1134
        unwrapped_fields376 = fields375
        self.write('(')
        self.write('values')
        self.newline()
        self.indent()
        for i378, elem377 in enumerate(unwrapped_fields376):
            
            if (i378 > 0):
                self.newline()
                _t1135 = None
            else:
                _t1135 = None
            _t1136 = self.pretty_var(elem377)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[Never]:
        def _t1137(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1138 = _dollar_dollar.rel_edb
            else:
                _t1138 = None
            return _t1138
        _t1139 = _t1137(msg)
        deconstruct_result381 = _t1139
        
        if deconstruct_result381 is not None:
            _t1141 = self.pretty_rel_edb(deconstruct_result381)
            _t1140 = _t1141
        else:
            def _t1142(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1143 = _dollar_dollar.betree_relation
                else:
                    _t1143 = None
                return _t1143
            _t1144 = _t1142(msg)
            deconstruct_result380 = _t1144
            
            if deconstruct_result380 is not None:
                _t1146 = self.pretty_betree_relation(deconstruct_result380)
                _t1145 = _t1146
            else:
                def _t1147(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1148 = _dollar_dollar.csv_data
                    else:
                        _t1148 = None
                    return _t1148
                _t1149 = _t1147(msg)
                deconstruct_result379 = _t1149
                
                if deconstruct_result379 is not None:
                    _t1151 = self.pretty_csv_data(deconstruct_result379)
                    _t1150 = _t1151
                else:
                    raise ParseError('No matching rule for data')
                _t1145 = _t1150
            _t1140 = _t1145
        return _t1140

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[Never]:
        def _t1152(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1153 = _t1152(msg)
        fields382 = _t1153
        unwrapped_fields383 = fields382
        self.write('(')
        self.write('rel_edb')
        self.newline()
        self.indent()
        field384 = unwrapped_fields383[0]
        _t1154 = self.pretty_relation_id(field384)
        self.newline()
        field385 = unwrapped_fields383[1]
        _t1155 = self.pretty_rel_edb_path(field385)
        self.newline()
        field386 = unwrapped_fields383[2]
        _t1156 = self.pretty_rel_edb_types(field386)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_rel_edb_path(self, msg: list[str]) -> Optional[Never]:
        def _t1157(_dollar_dollar):
            return _dollar_dollar
        _t1158 = _t1157(msg)
        fields387 = _t1158
        unwrapped_fields388 = fields387
        self.write('[')
        for i390, elem389 in enumerate(unwrapped_fields388):
            
            if (i390 > 0):
                self.newline()
                _t1159 = None
            else:
                _t1159 = None
            self.write(repr(elem389))
        self.write(']')
        return None

    def pretty_rel_edb_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1160(_dollar_dollar):
            return _dollar_dollar
        _t1161 = _t1160(msg)
        fields391 = _t1161
        unwrapped_fields392 = fields391
        self.write('[')
        for i394, elem393 in enumerate(unwrapped_fields392):
            
            if (i394 > 0):
                self.newline()
                _t1162 = None
            else:
                _t1162 = None
            _t1163 = self.pretty_type(elem393)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[Never]:
        def _t1164(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1165 = _t1164(msg)
        fields395 = _t1165
        unwrapped_fields396 = fields395
        self.write('(')
        self.write('betree_relation')
        self.newline()
        self.indent()
        field397 = unwrapped_fields396[0]
        _t1166 = self.pretty_relation_id(field397)
        self.newline()
        field398 = unwrapped_fields396[1]
        _t1167 = self.pretty_betree_info(field398)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[Never]:
        def _t1168(_dollar_dollar):
            _t1169 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1169,)
        _t1170 = _t1168(msg)
        fields399 = _t1170
        unwrapped_fields400 = fields399
        self.write('(')
        self.write('betree_info')
        self.newline()
        self.indent()
        field401 = unwrapped_fields400[0]
        _t1171 = self.pretty_betree_info_key_types(field401)
        self.newline()
        field402 = unwrapped_fields400[1]
        _t1172 = self.pretty_betree_info_value_types(field402)
        self.newline()
        field403 = unwrapped_fields400[2]
        _t1173 = self.pretty_config_dict(field403)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_betree_info_key_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1174(_dollar_dollar):
            return _dollar_dollar
        _t1175 = _t1174(msg)
        fields404 = _t1175
        unwrapped_fields405 = fields404
        self.write('(')
        self.write('key_types')
        self.newline()
        self.indent()
        for i407, elem406 in enumerate(unwrapped_fields405):
            
            if (i407 > 0):
                self.newline()
                _t1176 = None
            else:
                _t1176 = None
            _t1177 = self.pretty_type(elem406)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_betree_info_value_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1178(_dollar_dollar):
            return _dollar_dollar
        _t1179 = _t1178(msg)
        fields408 = _t1179
        unwrapped_fields409 = fields408
        self.write('(')
        self.write('value_types')
        self.newline()
        self.indent()
        for i411, elem410 in enumerate(unwrapped_fields409):
            
            if (i411 > 0):
                self.newline()
                _t1180 = None
            else:
                _t1180 = None
            _t1181 = self.pretty_type(elem410)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[Never]:
        def _t1182(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1183 = _t1182(msg)
        fields412 = _t1183
        unwrapped_fields413 = fields412
        self.write('(')
        self.write('csv_data')
        self.newline()
        self.indent()
        field414 = unwrapped_fields413[0]
        _t1184 = self.pretty_csvlocator(field414)
        self.newline()
        field415 = unwrapped_fields413[1]
        _t1185 = self.pretty_csv_config(field415)
        self.newline()
        field416 = unwrapped_fields413[2]
        _t1186 = self.pretty_csv_columns(field416)
        self.newline()
        field417 = unwrapped_fields413[3]
        _t1187 = self.pretty_csv_asof(field417)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[Never]:
        def _t1188(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1189 = _dollar_dollar.paths
            else:
                _t1189 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1190 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1190 = None
            return (_t1189, _t1190,)
        _t1191 = _t1188(msg)
        fields418 = _t1191
        unwrapped_fields419 = fields418
        self.write('(')
        self.write('csv_locator')
        self.newline()
        self.indent()
        field420 = unwrapped_fields419[0]
        
        if field420 is not None:
            opt_val421 = field420
            _t1193 = self.pretty_csv_locator_paths(opt_val421)
            _t1192 = _t1193
        else:
            _t1192 = None
        self.newline()
        field422 = unwrapped_fields419[1]
        
        if field422 is not None:
            opt_val423 = field422
            _t1195 = self.pretty_csv_locator_inline_data(opt_val423)
            _t1194 = _t1195
        else:
            _t1194 = None
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_locator_paths(self, msg: list[str]) -> Optional[Never]:
        def _t1196(_dollar_dollar):
            return _dollar_dollar
        _t1197 = _t1196(msg)
        fields424 = _t1197
        unwrapped_fields425 = fields424
        self.write('(')
        self.write('paths')
        self.newline()
        self.indent()
        for i427, elem426 in enumerate(unwrapped_fields425):
            
            if (i427 > 0):
                self.newline()
                _t1198 = None
            else:
                _t1198 = None
            self.write(repr(elem426))
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> Optional[Never]:
        def _t1199(_dollar_dollar):
            return _dollar_dollar
        _t1200 = _t1199(msg)
        fields428 = _t1200
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
        def _t1201(_dollar_dollar):
            _t1202 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1202
        _t1203 = _t1201(msg)
        fields430 = _t1203
        unwrapped_fields431 = fields430
        self.write('(')
        self.write('csv_config')
        self.newline()
        self.indent()
        _t1204 = self.pretty_config_dict(unwrapped_fields431)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_columns(self, msg: list[logic_pb2.CSVColumn]) -> Optional[Never]:
        def _t1205(_dollar_dollar):
            return _dollar_dollar
        _t1206 = _t1205(msg)
        fields432 = _t1206
        unwrapped_fields433 = fields432
        self.write('(')
        self.write('columns')
        self.newline()
        self.indent()
        for i435, elem434 in enumerate(unwrapped_fields433):
            
            if (i435 > 0):
                self.newline()
                _t1207 = None
            else:
                _t1207 = None
            _t1208 = self.pretty_csv_column(elem434)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[Never]:
        def _t1209(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1210 = _t1209(msg)
        fields436 = _t1210
        unwrapped_fields437 = fields436
        self.write('(')
        self.write('column')
        self.newline()
        self.indent()
        field438 = unwrapped_fields437[0]
        self.write(repr(field438))
        self.newline()
        field439 = unwrapped_fields437[1]
        _t1211 = self.pretty_relation_id(field439)
        self.write('[')
        self.newline()
        field440 = unwrapped_fields437[2]
        for i442, elem441 in enumerate(field440):
            
            if (i442 > 0):
                self.newline()
                _t1212 = None
            else:
                _t1212 = None
            _t1213 = self.pretty_type(elem441)
        self.write(']')
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[Never]:
        def _t1214(_dollar_dollar):
            return _dollar_dollar
        _t1215 = _t1214(msg)
        fields443 = _t1215
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
        def _t1216(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1217 = _t1216(msg)
        fields445 = _t1217
        unwrapped_fields446 = fields445
        self.write('(')
        self.write('undefine')
        self.newline()
        self.indent()
        _t1218 = self.pretty_fragment_id(unwrapped_fields446)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[Never]:
        def _t1219(_dollar_dollar):
            return _dollar_dollar.relations
        _t1220 = _t1219(msg)
        fields447 = _t1220
        unwrapped_fields448 = fields447
        self.write('(')
        self.write('context')
        self.newline()
        self.indent()
        for i450, elem449 in enumerate(unwrapped_fields448):
            
            if (i450 > 0):
                self.newline()
                _t1221 = None
            else:
                _t1221 = None
            _t1222 = self.pretty_relation_id(elem449)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_epoch_reads(self, msg: list[transactions_pb2.Read]) -> Optional[Never]:
        def _t1223(_dollar_dollar):
            return _dollar_dollar
        _t1224 = _t1223(msg)
        fields451 = _t1224
        unwrapped_fields452 = fields451
        self.write('(')
        self.write('reads')
        self.newline()
        self.indent()
        for i454, elem453 in enumerate(unwrapped_fields452):
            
            if (i454 > 0):
                self.newline()
                _t1225 = None
            else:
                _t1225 = None
            _t1226 = self.pretty_read(elem453)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[Never]:
        def _t1227(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1228 = _dollar_dollar.demand
            else:
                _t1228 = None
            return _t1228
        _t1229 = _t1227(msg)
        deconstruct_result459 = _t1229
        
        if deconstruct_result459 is not None:
            _t1231 = self.pretty_demand(deconstruct_result459)
            _t1230 = _t1231
        else:
            def _t1232(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1233 = _dollar_dollar.output
                else:
                    _t1233 = None
                return _t1233
            _t1234 = _t1232(msg)
            deconstruct_result458 = _t1234
            
            if deconstruct_result458 is not None:
                _t1236 = self.pretty_output(deconstruct_result458)
                _t1235 = _t1236
            else:
                def _t1237(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1238 = _dollar_dollar.what_if
                    else:
                        _t1238 = None
                    return _t1238
                _t1239 = _t1237(msg)
                deconstruct_result457 = _t1239
                
                if deconstruct_result457 is not None:
                    _t1241 = self.pretty_what_if(deconstruct_result457)
                    _t1240 = _t1241
                else:
                    def _t1242(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1243 = _dollar_dollar.abort
                        else:
                            _t1243 = None
                        return _t1243
                    _t1244 = _t1242(msg)
                    deconstruct_result456 = _t1244
                    
                    if deconstruct_result456 is not None:
                        _t1246 = self.pretty_abort(deconstruct_result456)
                        _t1245 = _t1246
                    else:
                        def _t1247(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1248 = _dollar_dollar.export
                            else:
                                _t1248 = None
                            return _t1248
                        _t1249 = _t1247(msg)
                        deconstruct_result455 = _t1249
                        
                        if deconstruct_result455 is not None:
                            _t1251 = self.pretty_export(deconstruct_result455)
                            _t1250 = _t1251
                        else:
                            raise ParseError('No matching rule for read')
                        _t1245 = _t1250
                    _t1240 = _t1245
                _t1235 = _t1240
            _t1230 = _t1235
        return _t1230

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[Never]:
        def _t1252(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1253 = _t1252(msg)
        fields460 = _t1253
        unwrapped_fields461 = fields460
        self.write('(')
        self.write('demand')
        self.newline()
        self.indent()
        _t1254 = self.pretty_relation_id(unwrapped_fields461)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[Never]:
        def _t1255(_dollar_dollar):
            
            if _dollar_dollar.name != 'output':
                _t1256 = _dollar_dollar.name
            else:
                _t1256 = None
            return (_t1256, _dollar_dollar.relation_id,)
        _t1257 = _t1255(msg)
        fields462 = _t1257
        unwrapped_fields463 = fields462
        self.write('(')
        self.write('output')
        self.newline()
        self.indent()
        field464 = unwrapped_fields463[0]
        
        if field464 is not None:
            opt_val465 = field464
            _t1259 = self.pretty_name(opt_val465)
            _t1258 = _t1259
        else:
            _t1258 = None
        self.newline()
        field466 = unwrapped_fields463[1]
        _t1260 = self.pretty_relation_id(field466)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[Never]:
        def _t1261(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1262 = _t1261(msg)
        fields467 = _t1262
        unwrapped_fields468 = fields467
        self.write('(')
        self.write('what_if')
        self.newline()
        self.indent()
        field469 = unwrapped_fields468[0]
        _t1263 = self.pretty_name(field469)
        self.newline()
        field470 = unwrapped_fields468[1]
        _t1264 = self.pretty_epoch(field470)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[Never]:
        def _t1265(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1266 = _dollar_dollar.name
            else:
                _t1266 = None
            return (_t1266, _dollar_dollar.relation_id,)
        _t1267 = _t1265(msg)
        fields471 = _t1267
        unwrapped_fields472 = fields471
        self.write('(')
        self.write('abort')
        self.newline()
        self.indent()
        field473 = unwrapped_fields472[0]
        
        if field473 is not None:
            opt_val474 = field473
            _t1269 = self.pretty_name(opt_val474)
            _t1268 = _t1269
        else:
            _t1268 = None
        self.newline()
        field475 = unwrapped_fields472[1]
        _t1270 = self.pretty_relation_id(field475)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[Never]:
        def _t1271(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1272 = _t1271(msg)
        fields476 = _t1272
        unwrapped_fields477 = fields476
        self.write('(')
        self.write('export')
        self.newline()
        self.indent()
        _t1273 = self.pretty_export_csv_config(unwrapped_fields477)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[Never]:
        def _t1274(_dollar_dollar):
            _t1275 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1275,)
        _t1276 = _t1274(msg)
        fields478 = _t1276
        unwrapped_fields479 = fields478
        self.write('(')
        self.write('export_csv_config')
        self.newline()
        self.indent()
        field480 = unwrapped_fields479[0]
        _t1277 = self.pretty_export_csv_path(field480)
        self.newline()
        field481 = unwrapped_fields479[1]
        _t1278 = self.pretty_export_csv_columns(field481)
        self.newline()
        field482 = unwrapped_fields479[2]
        _t1279 = self.pretty_config_dict(field482)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[Never]:
        def _t1280(_dollar_dollar):
            return _dollar_dollar
        _t1281 = _t1280(msg)
        fields483 = _t1281
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
        def _t1282(_dollar_dollar):
            return _dollar_dollar
        _t1283 = _t1282(msg)
        fields485 = _t1283
        unwrapped_fields486 = fields485
        self.write('(')
        self.write('columns')
        self.newline()
        self.indent()
        for i488, elem487 in enumerate(unwrapped_fields486):
            
            if (i488 > 0):
                self.newline()
                _t1284 = None
            else:
                _t1284 = None
            _t1285 = self.pretty_export_csv_column(elem487)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[Never]:
        def _t1286(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1287 = _t1286(msg)
        fields489 = _t1287
        unwrapped_fields490 = fields489
        self.write('(')
        self.write('column')
        self.newline()
        self.indent()
        field491 = unwrapped_fields490[0]
        self.write(repr(field491))
        self.newline()
        field492 = unwrapped_fields490[1]
        _t1288 = self.pretty_relation_id(field492)
        self.dedent()
        self.write(')')
        self.newline()
        return None

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if (value is not None and value.HasField('int_value')):
            return value.int_value
        return default

    def _extract_value_float64(self, value: Optional[logic_pb2.Value], default: float) -> float:
        if (value is not None and value.HasField('float_value')):
            return value.float_value
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if (value is not None and value.HasField('string_value')):
            return value.string_value
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if (value is not None and value.HasField('boolean_value')):
            return value.boolean_value
        return default

    def _extract_value_bytes(self, value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        if (value is not None and value.HasField('string_value')):
            return value.string_value.encode()
        return default

    def _extract_value_uint128(self, value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        if (value is not None and value.HasField('uint128_value')):
            return value.uint128_value
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: list[str]) -> list[str]:
        if (value is not None and value.HasField('string_value')):
            return [value.string_value]
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if (value is not None and value.HasField('int_value')):
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if (value is not None and value.HasField('float_value')):
            return value.float_value
        return None

    def _try_extract_value_string(self, value: Optional[logic_pb2.Value]) -> Optional[str]:
        if (value is not None and value.HasField('string_value')):
            return value.string_value
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if (value is not None and value.HasField('string_value')):
            return value.string_value.encode()
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if (value is not None and value.HasField('uint128_value')):
            return value.uint128_value
        return None

    def _try_extract_value_string_list(self, value: Optional[logic_pb2.Value]) -> Optional[list[str]]:
        if (value is not None and value.HasField('string_value')):
            return [value.string_value]
        return None

    def construct_csv_config(self, config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1289 = self._extract_value_int64(config.get('csv_header_row'), 1)
        header_row = _t1289
        _t1290 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1290
        _t1291 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1291
        _t1292 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1292
        _t1293 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1293
        _t1294 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1294
        _t1295 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t1295
        _t1296 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1296
        _t1297 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1297
        _t1298 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1298
        _t1299 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1299
        _t1300 = logic_pb2.CSVConfig(header_row=int(header_row), skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1300

    def construct_betree_info(self, key_types: list[logic_pb2.Type], value_types: list[logic_pb2.Type], config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1301 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1301
        _t1302 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1302
        _t1303 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1303
        _t1304 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1304
        _t1305 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1305
        _t1306 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1306
        _t1307 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1307
        _t1308 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1308
        _t1309 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1309
        _t1310 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1310
        _t1311 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1311

    def default_configure(self) -> transactions_pb2.Configure:
        _t1312 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1312
        _t1313 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1313

    def construct_configure(self, config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            if maintenance_level_val.string_value == 'off':
                maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
            else:
                if maintenance_level_val.string_value == 'auto':
                    maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
                else:
                    if maintenance_level_val.string_value == 'all':
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                    else:
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        _t1314 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1314
        _t1315 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1315
        _t1316 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1316

    def export_csv_config(self, path: str, columns: list[transactions_pb2.ExportCSVColumn], config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1317 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1317
        _t1318 = self._extract_value_string(config.get('compression'), '')
        compression = _t1318
        _t1319 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1319
        _t1320 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1320
        _t1321 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1321
        _t1322 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1322
        _t1323 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1323
        _t1324 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1324

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1325 = logic_pb2.Value(int_value=v)
        return _t1325

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1326 = logic_pb2.Value(float_value=v)
        return _t1326

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1327 = logic_pb2.Value(string_value=v)
        return _t1327

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1328 = logic_pb2.Value(boolean_value=v)
        return _t1328

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1329 = logic_pb2.Value(uint128_value=v)
        return _t1329

    def is_default_configure(self, cfg: transactions_pb2.Configure) -> bool:
        if cfg.semantics_version != 0:
            return False
        if cfg.ivm_config.level != transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
            return False
        return True

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if msg.semantics_version != 0:
            _t1331 = self._make_value_int64(msg.semantics_version)
            result.append(('semantics_version', _t1331,))
            _t1330 = None
        else:
            _t1330 = None
        
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1333 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1333,))
            _t1332 = None
        else:
            
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1335 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1335,))
                _t1334 = None
            else:
                
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1337 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1337,))
                    _t1336 = None
                else:
                    _t1336 = None
                _t1334 = _t1336
            _t1332 = _t1334
        return result

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if msg.header_row != 1:
            _t1339 = self._make_value_int64(int(msg.header_row))
            result.append(('csv_header_row', _t1339,))
            _t1338 = None
        else:
            _t1338 = None
        
        if msg.skip != 0:
            _t1341 = self._make_value_int64(msg.skip)
            result.append(('csv_skip', _t1341,))
            _t1340 = None
        else:
            _t1340 = None
        
        if msg.new_line != '':
            _t1343 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1343,))
            _t1342 = None
        else:
            _t1342 = None
        
        if msg.delimiter != ',':
            _t1345 = self._make_value_string(msg.delimiter)
            result.append(('csv_delimiter', _t1345,))
            _t1344 = None
        else:
            _t1344 = None
        
        if msg.quotechar != '"':
            _t1347 = self._make_value_string(msg.quotechar)
            result.append(('csv_quotechar', _t1347,))
            _t1346 = None
        else:
            _t1346 = None
        
        if msg.escapechar != '"':
            _t1349 = self._make_value_string(msg.escapechar)
            result.append(('csv_escapechar', _t1349,))
            _t1348 = None
        else:
            _t1348 = None
        
        if msg.comment != '':
            _t1351 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1351,))
            _t1350 = None
        else:
            _t1350 = None
        
        if not len(msg.missing_strings) == 0:
            _t1353 = self._make_value_string(msg.missing_strings[0])
            result.append(('csv_missing_strings', _t1353,))
            _t1352 = None
        else:
            _t1352 = None
        
        if msg.decimal_separator != '.':
            _t1355 = self._make_value_string(msg.decimal_separator)
            result.append(('csv_decimal_separator', _t1355,))
            _t1354 = None
        else:
            _t1354 = None
        
        if msg.encoding != 'utf-8':
            _t1357 = self._make_value_string(msg.encoding)
            result.append(('csv_encoding', _t1357,))
            _t1356 = None
        else:
            _t1356 = None
        
        if msg.compression != 'auto':
            _t1359 = self._make_value_string(msg.compression)
            result.append(('csv_compression', _t1359,))
            _t1358 = None
        else:
            _t1358 = None
        return result

    def _maybe_push_float64(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[float]) -> None:
        
        if val is not None:
            _t1361 = self._make_value_float64(val)
            result.append((key, _t1361,))
            _t1360 = None
        else:
            _t1360 = None
        return None

    def _maybe_push_int64(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[int]) -> None:
        
        if val is not None:
            _t1363 = self._make_value_int64(val)
            result.append((key, _t1363,))
            _t1362 = None
        else:
            _t1362 = None
        return None

    def _maybe_push_uint128(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[logic_pb2.UInt128Value]) -> None:
        
        if val is not None:
            _t1365 = self._make_value_uint128(val)
            result.append((key, _t1365,))
            _t1364 = None
        else:
            _t1364 = None
        return None

    def _maybe_push_bytes_as_string(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[bytes]) -> None:
        
        if val is not None:
            _t1367 = self._make_value_string(val.decode('utf-8'))
            result.append((key, _t1367,))
            _t1366 = None
        else:
            _t1366 = None
        return None

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1368 = self._maybe_push_float64(result, 'betree_config_epsilon', msg.storage_config.epsilon)
        _t1369 = self._maybe_push_int64(result, 'betree_config_max_pivots', msg.storage_config.max_pivots)
        _t1370 = self._maybe_push_int64(result, 'betree_config_max_deltas', msg.storage_config.max_deltas)
        _t1371 = self._maybe_push_int64(result, 'betree_config_max_leaf', msg.storage_config.max_leaf)
        _t1372 = self._maybe_push_uint128(result, 'betree_locator_root_pageid', msg.relation_locator.root_pageid)
        _t1373 = self._maybe_push_bytes_as_string(result, 'betree_locator_inline_data', msg.relation_locator.inline_data)
        _t1374 = self._maybe_push_int64(result, 'betree_locator_element_count', msg.relation_locator.element_count)
        _t1375 = self._maybe_push_int64(result, 'betree_locator_tree_height', msg.relation_locator.tree_height)
        return result

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if (msg.partition_size is not None and msg.partition_size != 0):
            _t1377 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1377,))
            _t1376 = None
        else:
            _t1376 = None
        
        if (msg.compression is not None and msg.compression != ''):
            _t1379 = self._make_value_string(msg.compression)
            result.append(('compression', _t1379,))
            _t1378 = None
        else:
            _t1378 = None
        
        if msg.syntax_header_row is not None:
            _t1381 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1381,))
            _t1380 = None
        else:
            _t1380 = None
        
        if (msg.syntax_missing_string is not None and msg.syntax_missing_string != ''):
            _t1383 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1383,))
            _t1382 = None
        else:
            _t1382 = None
        
        if (msg.syntax_delim is not None and msg.syntax_delim != ','):
            _t1385 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1385,))
            _t1384 = None
        else:
            _t1384 = None
        
        if (msg.syntax_quotechar is not None and msg.syntax_quotechar != '"'):
            _t1387 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1387,))
            _t1386 = None
        else:
            _t1386 = None
        
        if (msg.syntax_escapechar is not None and msg.syntax_escapechar != '\\'):
            _t1389 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1389,))
            _t1388 = None
        else:
            _t1388 = None
        return result

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != '':
            return name
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == '':
            return self.relation_id_to_uint128(msg)
        return None

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        return (abs.vars, [],)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    return printer.get_output()
