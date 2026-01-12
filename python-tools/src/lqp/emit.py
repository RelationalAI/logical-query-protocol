import lqp.ir as ir
from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2
from typing import Union, Dict, Any
from functools import reduce

# Maps ir.TypeNames to the associated Proto message for *non-paremetric types*. Used to generically construct non-parametric types.
# Parametric types should be handled in convert_type
non_parametric_types = {
    ir.TypeName.UNSPECIFIED: "UnspecifiedType",
    ir.TypeName.STRING: "StringType",
    ir.TypeName.INT: "IntType",
    ir.TypeName.FLOAT: "FloatType",
    ir.TypeName.UINT128: "UInt128Type",
    ir.TypeName.INT128: "Int128Type",
    ir.TypeName.DATE: "DateType",
    ir.TypeName.DATETIME: "DateTimeType",
    ir.TypeName.MISSING: "MissingType",
    ir.TypeName.BOOLEAN: "BooleanType",
}

def convert_type(rt: ir.Type) -> logic_pb2.Type:
    if rt.type_name == ir.TypeName.DECIMAL :
        assert isinstance(rt.parameters[0].value, int) and isinstance(rt.parameters[1].value, int), "DECIMAL parameters are not integers"
        assert len(rt.parameters) == 2, f"DECIMAL parameters should have only precision and scale, got {len(rt.parameters)} arguments"
        assert rt.parameters[0].value <= 38, f"DECIMAL precision must be less than 38, got {rt.parameters[0]}"
        assert rt.parameters[1].value <= rt.parameters[0].value, f"DECIMAL precision ({rt.parameters[0]}) must be at least scale ({rt.parameters[1]})"
        return logic_pb2.Type(
            decimal_type=logic_pb2.DecimalType(
                precision=rt.parameters[0].value, scale=rt.parameters[1].value
            )
        )
    else:
        cls = getattr(logic_pb2, non_parametric_types[rt.type_name])
        return logic_pb2.Type(**{str(rt.type_name).lower()+"_type": cls()})

def convert_uint128(val: ir.UInt128Value) -> logic_pb2.UInt128Value:
    low = val.value & 0xFFFFFFFFFFFFFFFF
    high = (val.value >> 64) & 0xFFFFFFFFFFFFFFFF
    return logic_pb2.UInt128Value(low=low, high=high)

def convert_int128(val: ir.Int128Value) -> logic_pb2.Int128Value:
    low = val.value & 0xFFFFFFFFFFFFFFFF
    high = (val.value >> 64) & 0xFFFFFFFFFFFFFFFF
    return logic_pb2.Int128Value(low=low, high=high)

def convert_date(val: ir.DateValue) -> logic_pb2.DateValue:
    return logic_pb2.DateValue(year=val.value.year, month=val.value.month, day=val.value.day)

def convert_datetime(val: ir.DateTimeValue) -> logic_pb2.DateTimeValue:
    return logic_pb2.DateTimeValue(
        year=val.value.year,
        month=val.value.month,
        day=val.value.day,
        hour=val.value.hour,
        minute=val.value.minute,
        second=val.value.second,
        microsecond=val.value.microsecond
    )

def convert_decimal(val: ir.DecimalValue) -> logic_pb2.DecimalValue:
    sign, digits, exponent = val.value.as_tuple()
    value = reduce(lambda rst, d: rst * 10 + d, digits)

    assert isinstance(exponent, int)
    assert isinstance(value, int)

    # Adjust value by the exponent. Python's decimal values are (sign, digits, exponent),
    # so if we have digits 12300 with exponent -4, but we need `scale` of 6, then we need to
    # multiply the digits by 10 ** 2 (i.e., 10 ** (6 + -4)) to get the physical value of
    # 1230000.
    # Ensure we stay in the integer realm when the exponent outweighs the scale, e.g.
    # value = 4.4000000000000003552713678800500929355621337890625
    modifier = val.scale + exponent
    if modifier >= 0:
        value *= 10 ** modifier
    else:
        value //= 10 ** (-modifier)

    if sign == 1:
        value = -value

    value = ir.Int128Value(value=value, meta=val.meta)

    return logic_pb2.DecimalValue(
        precision=val.precision,
        scale=val.scale,
        value=convert_int128(value),
    )

def convert_value(pv: ir.Value) -> logic_pb2.Value:
    if isinstance(pv.value, str):
        return logic_pb2.Value(string_value=pv.value)
    elif isinstance(pv.value, ir.MissingValue):
        return logic_pb2.Value(missing_value=logic_pb2.MissingValue())
    elif isinstance(pv.value, int):
        assert pv.value.bit_length() <= 64, "Integer value exceeds 64 bits"
        return logic_pb2.Value(int_value=pv.value)
    elif isinstance(pv.value, float):
        return logic_pb2.Value(float_value=pv.value)
    elif isinstance(pv.value, ir.UInt128Value):
        return logic_pb2.Value(
            uint128_value=convert_uint128(pv.value)
        )
    elif isinstance(pv.value, ir.Int128Value):
        return logic_pb2.Value(
            int128_value=convert_int128(pv.value)
        )
    elif isinstance(pv.value, ir.DateValue):
        return logic_pb2.Value(
            date_value=convert_date(pv.value)
        )
    elif isinstance(pv.value, ir.DateTimeValue):
        return logic_pb2.Value(
            datetime_value=convert_datetime(pv.value)
        )
    elif isinstance(pv.value, ir.DecimalValue):
        return logic_pb2.Value(
            decimal_value=convert_decimal(pv.value)
        )
    elif isinstance(pv.value, ir.BooleanValue):
        return logic_pb2.Value(boolean_value=pv.value.value)
    else:
        raise TypeError(f"Unsupported Value type: {type(pv.value)}")

def convert_var(v: ir.Var) -> logic_pb2.Var:
    return logic_pb2.Var(name=v.name)

def convert_term(t: ir.Term) -> logic_pb2.Term:
    if isinstance(t, ir.Var):
        return logic_pb2.Term(var=convert_var(t))
    else:
        return logic_pb2.Term(constant=convert_value(t))

def convert_relterm(t: ir.RelTerm) -> logic_pb2.RelTerm:
    if isinstance(t, ir.SpecializedValue):
        return logic_pb2.RelTerm(specialized_value=convert_value(t.value))
    else:
        return logic_pb2.RelTerm(term=convert_term(t))

def convert_relation_id(rid: ir.RelationId) -> logic_pb2.RelationId:
    id_low = rid.id & 0xFFFFFFFFFFFFFFFF
    id_high = (rid.id >> 64) & 0xFFFFFFFFFFFFFFFF
    return logic_pb2.RelationId(id_low=id_low, id_high=id_high)

def convert_fragment_id(fid: ir.FragmentId) -> fragments_pb2.FragmentId:
    return fragments_pb2.FragmentId(id=fid.id)

def convert_attribute(attr: ir.Attribute) -> logic_pb2.Attribute:
    return logic_pb2.Attribute(
        name=attr.name,
        args=[convert_value(arg) for arg in attr.args]
)

def convert_abstraction(abst: ir.Abstraction) -> logic_pb2.Abstraction:
    bindings = [logic_pb2.Binding(var=convert_var(var_tuple[0]), type=convert_type(var_tuple[1]))
                for var_tuple in abst.vars]
    return logic_pb2.Abstraction(
        vars=bindings,
        value=convert_formula(abst.value)
    )

def convert_formula(f: ir.Formula) -> logic_pb2.Formula:
    if isinstance(f, ir.Exists):
        return logic_pb2.Formula(exists=logic_pb2.Exists(body=convert_abstraction(f.body)))
    elif isinstance(f, ir.Reduce):
        return logic_pb2.Formula(reduce=logic_pb2.Reduce(
            op=convert_abstraction(f.op),
            body=convert_abstraction(f.body),
            terms=[convert_term(t) for t in f.terms]
        ))
    elif isinstance(f, ir.Conjunction):
        return logic_pb2.Formula(conjunction=logic_pb2.Conjunction(args=[convert_formula(arg) for arg in f.args]))
    elif isinstance(f, ir.Disjunction):
        return logic_pb2.Formula(disjunction=logic_pb2.Disjunction(args=[convert_formula(arg) for arg in f.args]))
    elif isinstance(f, ir.Not):
        return logic_pb2.Formula(**{"not": logic_pb2.Not(arg=convert_formula(f.arg))}) # type: ignore
    elif isinstance(f, ir.FFI):
        return logic_pb2.Formula(ffi=logic_pb2.FFI(
            name=f.name,
            args=[convert_abstraction(arg) for arg in f.args],
            terms=[convert_term(t) for t in f.terms]
        ))
    elif isinstance(f, ir.Atom):
        return logic_pb2.Formula(atom=logic_pb2.Atom(
            name=convert_relation_id(f.name),
            terms=[convert_term(t) for t in f.terms]
        ))
    elif isinstance(f, ir.Pragma):
        return logic_pb2.Formula(pragma=logic_pb2.Pragma(
            name=f.name,
            terms=[convert_term(t) for t in f.terms]
        ))
    elif isinstance(f, ir.Primitive):
        primitive_proto = logic_pb2.Primitive(name=f.name, terms=[convert_relterm(t) for t in f.terms])
        return logic_pb2.Formula(primitive=primitive_proto)
    elif isinstance(f, ir.RelAtom):
        rel_atom_proto = logic_pb2.RelAtom(name=f.name, terms=[convert_relterm(t) for t in f.terms])
        return logic_pb2.Formula(rel_atom=rel_atom_proto)
    elif isinstance(f, ir.Cast):
        return logic_pb2.Formula(cast=logic_pb2.Cast(
            input=convert_term(f.input),
            result=convert_term(f.result)
        ))
    else:
        raise TypeError(f"Unsupported Formula type: {type(f)}")

def convert_betree_config(config: ir.BeTreeConfig) -> logic_pb2.BeTreeConfig:
    return logic_pb2.BeTreeConfig(
        epsilon=config.epsilon,
        max_pivots=config.max_pivots,
        max_deltas=config.max_deltas,
        max_leaf=config.max_leaf
    )

def convert_betree_locator(locator: ir.BeTreeLocator) -> logic_pb2.BeTreeLocator:
    # Handle oneof: only set the location field that is not None
    kwargs: Dict[str, Any] = {
        'element_count': locator.element_count,
        'tree_height': locator.tree_height
    }
    if locator.root_pageid is not None:
        kwargs['root_pageid'] = convert_uint128(locator.root_pageid)
    if locator.inline_data is not None:
        kwargs['inline_data'] = locator.inline_data
    return logic_pb2.BeTreeLocator(**kwargs)

def convert_betree_info(info: ir.BeTreeInfo) -> logic_pb2.BeTreeInfo:
    return logic_pb2.BeTreeInfo(
        key_types=[convert_type(kt) for kt in info.key_types],
        value_types=[convert_type(vt) for vt in info.value_types],
        storage_config=convert_betree_config(info.storage_config),
        relation_locator=convert_betree_locator(info.relation_locator)
    )

def convert_rel_edb(rel: ir.RelEDB) -> logic_pb2.RelEDB:
    return logic_pb2.RelEDB(
        target_id=convert_relation_id(rel.target_id),
        path=rel.path,
        types=[convert_type(t) for t in rel.types]
    )

def convert_betree_relation(rel: ir.BeTreeRelation) -> logic_pb2.BeTreeRelation:
    return logic_pb2.BeTreeRelation(
        name=convert_relation_id(rel.name),
        relation_info=convert_betree_info(rel.relation_info)
    )

def convert_csv_locator(locator: ir.CSVLocator) -> logic_pb2.CSVLocator:
    kwargs: Dict[str, Any] = {}
    if locator.paths:
        kwargs['paths'] = locator.paths
    if locator.inline_data is not None:
        kwargs['inline_data'] = locator.inline_data
    return logic_pb2.CSVLocator(**kwargs)

def convert_csv_config(config: ir.CSVConfig) -> logic_pb2.CSVConfig:
    return logic_pb2.CSVConfig(
        header_row=config.header_row,
        skip=config.skip,
        new_line=config.new_line,
        delimiter=config.delimiter,
        quotechar=config.quotechar,
        escapechar=config.escapechar,
        comment=config.comment,
        missing_strings=list(config.missing_strings),
        decimal_separator=config.decimal_separator,
        encoding=config.encoding,
        compression=config.compression
    )

def convert_csv_column(column: ir.CSVColumn) -> logic_pb2.CSVColumn:
    return logic_pb2.CSVColumn(
        column_name=column.column_name,
        target_id=convert_relation_id(column.target_id),
        types=[convert_type(t) for t in column.types]
    )

def convert_csv_relation(rel: ir.CSVData) -> logic_pb2.CSVData:
    return logic_pb2.CSVData(
        locator=convert_csv_locator(rel.locator),
        config=convert_csv_config(rel.config),
        columns=[convert_csv_column(col) for col in rel.columns],
        asof=rel.asof
    )

def convert_data(data: ir.Data) -> logic_pb2.Data:
    if isinstance(data, ir.RelEDB):
        return logic_pb2.Data(rel_edb=convert_rel_edb(data))
    elif isinstance(data, ir.BeTreeRelation):
        return logic_pb2.Data(betree_relation=convert_betree_relation(data))
    elif isinstance(data, ir.CSVData):
        return logic_pb2.Data(csv_data=convert_csv_relation(data))
    else:
        raise TypeError(f"Unsupported Data type: {type(data)}")

def convert_def(d: ir.Def) -> logic_pb2.Def:
    return logic_pb2.Def(
        name=convert_relation_id(d.name),
        body=convert_abstraction(d.body),
        attrs=[convert_attribute(attr) for attr in d.attrs]
    )

def convert_loop(l: ir.Loop) -> logic_pb2.Loop:
    return logic_pb2.Loop(
        init=[convert_instruction(init_def) for init_def in l.init],
        body=convert_script(l.body)
    )

def convert_declaration(decl: ir.Declaration) -> logic_pb2.Declaration:
    from typing import Dict, Any
    if isinstance(decl, ir.Def):
        decl_dict: Dict[str, Any] = {'def': convert_def(decl)}
        return logic_pb2.Declaration(**decl_dict)  # type: ignore
    elif isinstance(decl, ir.Algorithm):
        algorithm_dict: Dict[str, Any] = {'algorithm': convert_algorithm(decl)}
        return logic_pb2.Declaration(**algorithm_dict)
    elif isinstance(decl, ir.Constraint):
        constraint_dict: Dict[str, Any] = {'constraint': convert_constraint(decl)}
        return logic_pb2.Declaration(**constraint_dict)
    elif isinstance(decl, ir.Data):
        data_dict: Dict[str, Any] = {'data': convert_data(decl)}
        return logic_pb2.Declaration(**data_dict)  # type: ignore
    else:
        raise TypeError(f"Unsupported Declaration type: {type(decl)}")

def convert_constraint(constraint: ir.Constraint) -> logic_pb2.Constraint:
    if isinstance(constraint, ir.FunctionalDependency):
        return logic_pb2.Constraint(
            functional_dependency=logic_pb2.FunctionalDependency(
                guard=convert_abstraction(constraint.guard),
                keys=[convert_var(v) for v in constraint.keys],
                values=[convert_var(v) for v in constraint.values],
            )
        )
    else:
        raise TypeError(f"Unsupported Constraint type: {type(constraint)}")

def convert_algorithm(algo: ir.Algorithm)-> logic_pb2.Algorithm:
    dict: Dict[str, Any] = {
        'global': [convert_relation_id(id) for id in algo.global_],
        'body':convert_script(algo.body)
    }
    return logic_pb2.Algorithm(**dict)

def convert_instruction(instr: ir.Instruction) -> logic_pb2.Instruction:
    from typing import Dict, Any
    if isinstance(instr, ir.Assign):
        dict: Dict[str, Any] = {'assign': convert_assign(instr)}
        return logic_pb2.Instruction(**dict)
    elif isinstance(instr, ir.Break):
        dict: Dict[str, Any] = {'break': convert_break(instr)}
        return logic_pb2.Instruction(**dict)
    elif isinstance(instr, ir.Upsert):
        dict: Dict[str, Any] = {'upsert': convert_upsert(instr)}
        return logic_pb2.Instruction(**dict)
    elif isinstance(instr, ir.MonoidDef):
        dict: Dict[str, Any] = {'monoid_def': convert_monoid_def(instr)}
        return logic_pb2.Instruction(**dict)
    elif isinstance(instr, ir.MonusDef):
        dict: Dict[str, Any] = {'monus_def': convert_monus_def(instr)}
        return logic_pb2.Instruction(**dict)
    else:
        raise TypeError(f"Unsupported Instruction type: {type(instr)}")

def convert_assign(instr: ir.Assign) -> logic_pb2.Assign:
    return logic_pb2.Assign(
        name=convert_relation_id(instr.name),
        body=convert_abstraction(instr.body),
        attrs=[convert_attribute(attr) for attr in instr.attrs]
    )
def convert_break(instr: ir.Break) -> logic_pb2.Break:
    return logic_pb2.Break(
        name=convert_relation_id(instr.name),
        body=convert_abstraction(instr.body),
        attrs=[convert_attribute(attr) for attr in instr.attrs]
    )
def convert_upsert(instr: ir.Upsert) -> logic_pb2.Upsert:
    return logic_pb2.Upsert(
        value_arity=instr.value_arity,
        name=convert_relation_id(instr.name),
        body=convert_abstraction(instr.body),
        attrs=[convert_attribute(attr) for attr in instr.attrs]
    )
def convert_monoid_def(instr: ir.MonoidDef) -> logic_pb2.MonoidDef:
    return logic_pb2.MonoidDef(
        value_arity=instr.value_arity,
        monoid=convert_monoid(instr.monoid),
        name=convert_relation_id(instr.name),
        body=convert_abstraction(instr.body),
        attrs=[convert_attribute(attr) for attr in instr.attrs]
    )
def convert_monus_def(instr: ir.MonusDef) -> logic_pb2.MonusDef:
    return logic_pb2.MonusDef(
        value_arity=instr.value_arity,
        monoid=convert_monoid(instr.monoid),
        name=convert_relation_id(instr.name),
        body=convert_abstraction(instr.body),
        attrs=[convert_attribute(attr) for attr in instr.attrs]
    )
def convert_monoid(monoid: ir.Monoid) -> logic_pb2.Monoid:
    from typing import Dict, Any
    if isinstance(monoid, ir.OrMonoid):
        return logic_pb2.Monoid(**{'or_monoid': logic_pb2.OrMonoid()})  # type: ignore
    elif isinstance(monoid, ir.SumMonoid):
        type = convert_type(monoid.type)
        return logic_pb2.Monoid(**{'sum_monoid': logic_pb2.SumMonoid(type=type)})  # type: ignore
    elif isinstance(monoid, ir.MinMonoid):
        type = convert_type(monoid.type)
        return logic_pb2.Monoid(**{'min_monoid': logic_pb2.MinMonoid(type=type)})  # type: ignore
    elif isinstance(monoid, ir.MaxMonoid):
        type = convert_type(monoid.type)
        return logic_pb2.Monoid(**{'max_monoid': logic_pb2.MaxMonoid(type=type)})  # type: ignore
    else:
        raise TypeError(f"Unsupported Monoid: {monoid}")


def convert_script(script: ir.Script) -> logic_pb2.Script:
    return logic_pb2.Script(constructs=[convert_construct(c) for c in script.constructs])

def convert_construct(construct: ir.Construct) -> logic_pb2.Construct:
    from typing import Dict, Any
    if isinstance(construct, ir.Loop):
        loop_dict: Dict[str, Any] = {'loop': convert_loop(construct)}
        return logic_pb2.Construct(**loop_dict)  # type: ignore
    elif isinstance(construct, ir.Instruction):
        instruction_dict: Dict[str, Any] = {'instruction': convert_instruction(construct)}
        return logic_pb2.Construct(**instruction_dict)
    else:
        raise TypeError(f"Unsupported Construct type: {type(construct)}")

def convert_fragment(frag: ir.Fragment) -> fragments_pb2.Fragment:
    return fragments_pb2.Fragment(
        id=convert_fragment_id(frag.id),
        declarations=[convert_declaration(decl) for decl in frag.declarations],
        debug_info=convert_debug_info(frag.debug_info)
    )

def convert_debug_info(info: ir.DebugInfo) -> fragments_pb2.DebugInfo:
    return fragments_pb2.DebugInfo(
        ids=[convert_relation_id(key) for key in info.id_to_orig_name.keys()],
        orig_names=info.id_to_orig_name.values()
    )

def convert_define(d: ir.Define) -> transactions_pb2.Define:
    return transactions_pb2.Define(fragment=convert_fragment(d.fragment))

def convert_undefine(u: ir.Undefine) -> transactions_pb2.Undefine:
    return transactions_pb2.Undefine(fragment_id=convert_fragment_id(u.fragment_id))

def convert_context(c: ir.Context) -> transactions_pb2.Context:
    return transactions_pb2.Context(relations=[convert_relation_id(rid) for rid in c.relations])

def convert_write(w: ir.Write) -> transactions_pb2.Write:
    wt = w.write_type
    if isinstance(wt, ir.Define):
        return transactions_pb2.Write(define=convert_define(wt))
    elif isinstance(wt, ir.Undefine):
        return transactions_pb2.Write(undefine=convert_undefine(wt))
    elif isinstance(wt, ir.Context):
        return transactions_pb2.Write(context=convert_context(wt))
    else:
        raise TypeError(f"Unsupported Write type: {type(wt)}")

def convert_demand(d: ir.Demand) -> transactions_pb2.Demand:
    return transactions_pb2.Demand(relation_id=convert_relation_id(d.relation_id))

def convert_output(o: ir.Output) -> transactions_pb2.Output:
    kwargs: Dict[str, Any] = {'relation_id': convert_relation_id(o.relation_id)}
    if o.name is not None:
        kwargs['name'] = o.name
    return transactions_pb2.Output(**kwargs) # type: ignore

def convert_export(e: ir.Export) -> transactions_pb2.Export:
    return transactions_pb2.Export(csv_config=convert_export_config(e.config)) # type: ignore

def convert_export_config(ec: ir.ExportCSVConfig) -> transactions_pb2.ExportCSVConfig:
    return transactions_pb2.ExportCSVConfig(
        data_columns=[convert_export_csv_column(c) for c in ec.data_columns],
        path=ec.path,
        partition_size=ec.partition_size if ec.partition_size is not None else 0,
        compression=ec.compression if ec.compression is not None else "",
        syntax_header_row=ec.syntax_header_row if ec.syntax_header_row is not None else True, # type: ignore
        syntax_missing_string=ec.syntax_missing_string if ec.syntax_missing_string is not None else "",
        syntax_delim=ec.syntax_delim if ec.syntax_delim is not None else ",",
        syntax_quotechar=ec.syntax_quotechar if ec.syntax_quotechar is not None else '"',
        syntax_escapechar=ec.syntax_escapechar if ec.syntax_escapechar is not None else '\\'
    )

def convert_export_csv_column(ec: ir.ExportCSVColumn) -> transactions_pb2.ExportCSVColumn:
    return transactions_pb2.ExportCSVColumn(
        column_name=ec.column_name,
        column_data=convert_relation_id(ec.column_data),
    )

def convert_abort(a: ir.Abort) -> transactions_pb2.Abort:
    kwargs: Dict[str, Any] = {'relation_id': convert_relation_id(a.relation_id)}
    if a.name is not None:
        kwargs['name'] = a.name
    return transactions_pb2.Abort(**kwargs) # type: ignore

def convert_whatif(wi: ir.WhatIf) -> transactions_pb2.WhatIf:
    kwargs: Dict[str, Any] = {'epoch': convert_epoch(wi.epoch)}
    if wi.branch is not None:
        kwargs['branch'] = wi.branch
    return transactions_pb2.WhatIf(**kwargs) # type: ignore

def convert_read(r: ir.Read) -> transactions_pb2.Read:
    rt = r.read_type
    if isinstance(rt, ir.Demand):
        return transactions_pb2.Read(demand=convert_demand(rt))
    elif isinstance(rt, ir.Output):
        return transactions_pb2.Read(output=convert_output(rt))
    elif isinstance(rt, ir.WhatIf):
        return transactions_pb2.Read(what_if=convert_whatif(rt)) # Note the underscore
    elif isinstance(rt, ir.Abort):
        return transactions_pb2.Read(abort=convert_abort(rt))
    elif isinstance(rt, ir.Export):
        return transactions_pb2.Read(export=convert_export(rt))
    else:
        raise TypeError(f"Unsupported Read type: {type(rt)}")

def convert_epoch(e: ir.Epoch) -> transactions_pb2.Epoch:
    return transactions_pb2.Epoch(
        writes=[convert_write(w) for w in e.writes],
        reads=[convert_read(r) for r in e.reads]
    )

def convert_configure(c: ir.Configure) -> transactions_pb2.Configure:
    return transactions_pb2.Configure(
        semantics_version=c.semantics_version,
        ivm_config=convert_ivm_config(c.ivm_config)
    )

def convert_ivm_config(c: ir.IVMConfig) -> transactions_pb2.IVMConfig:
    return transactions_pb2.IVMConfig(
        level=convert_maintenance_level(c.level)
    )

def convert_maintenance_level(l: ir.MaintenanceLevel) -> transactions_pb2.MaintenanceLevel:
    return transactions_pb2.MaintenanceLevel.Name(l.value) # type: ignore[missing-attribute]

def convert_sync(c: ir.Sync) -> transactions_pb2.Sync:
    return transactions_pb2.Sync(fragments=[convert_fragment_id(rid) for rid in c.fragments])

def convert_transaction(t: ir.Transaction) -> transactions_pb2.Transaction:
    kwargs: Dict[str, Any] = {
        'configure': convert_configure(t.configure),
        'epochs': [convert_epoch(e) for e in t.epochs]
    }
    if t.sync is not None:
        kwargs['sync'] = convert_sync(t.sync)
    return transactions_pb2.Transaction(**kwargs)

def ir_to_proto(node: ir.LqpNode) -> Union[
    transactions_pb2.Transaction,
    fragments_pb2.Fragment,
    logic_pb2.Declaration,
    logic_pb2.Formula
]:
    if isinstance(node, ir.Transaction):
        return convert_transaction(node)
    elif isinstance(node, ir.Fragment):
        return convert_fragment(node)
    elif isinstance(node, ir.Declaration):
        return convert_declaration(node)
    elif isinstance(node, ir.Formula):
        return convert_formula(node)
    else:
        raise TypeError(f"Unsupported top-level IR node type for conversion: {type(node)}")
