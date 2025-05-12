import lqp.ir as ir
from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2
from typing import Union, Dict, Any

def convert_primitive_type(pt: ir.PrimitiveType) -> logic_pb2.PrimitiveType:
    if pt == ir.PrimitiveType.STRING:
        return logic_pb2.PRIMITIVE_TYPE_STRING
    elif pt == ir.PrimitiveType.INT:
        return logic_pb2.PRIMITIVE_TYPE_INT
    elif pt == ir.PrimitiveType.FLOAT:
        return logic_pb2.PRIMITIVE_TYPE_FLOAT
    elif pt == ir.PrimitiveType.UINT128:
        return logic_pb2.PRIMITIVE_TYPE_UINT128
    else:
        return logic_pb2.PRIMITIVE_TYPE_UNSPECIFIED

def convert_rel_value_type(rvt: ir.RelValueType) -> logic_pb2.RelValueType:
    try:
        return getattr(logic_pb2.RelValueType, f"REL_VALUE_TYPE_{rvt.name}")
    except AttributeError:
        return logic_pb2.REL_VALUE_TYPE_UNSPECIFIED

def convert_rel_type(rt: ir.RelType) -> logic_pb2.RelType:
    if isinstance(rt, ir.PrimitiveType):
        return logic_pb2.RelType(primitive_type=convert_primitive_type(rt))
    elif isinstance(rt, ir.RelValueType):
        return logic_pb2.RelType(value_type=convert_rel_value_type(rt))
    else:
        # Default or error case
        return logic_pb2.RelType(primitive_type=logic_pb2.PRIMITIVE_TYPE_UNSPECIFIED)

def convert_uint128(val: ir.UInt128) -> logic_pb2.UInt128:
    return logic_pb2.UInt128(low=val.low, high=val.high)

def convert_primitive_value(pv: ir.PrimitiveValue) -> logic_pb2.PrimitiveValue:
    if isinstance(pv, str):
        return logic_pb2.PrimitiveValue(string_value=pv)
    elif isinstance(pv, int):
        return logic_pb2.PrimitiveValue(int_value=pv)
    elif isinstance(pv, float):
        return logic_pb2.PrimitiveValue(float_value=pv)
    elif isinstance(pv, ir.UInt128):
        return logic_pb2.PrimitiveValue(uint128_value=convert_uint128(pv))
    else:
        raise TypeError(f"Unsupported PrimitiveValue type: {type(pv)}")

def convert_constant(c: ir.Constant) -> logic_pb2.Constant:
    return logic_pb2.Constant(value=convert_primitive_value(c))

def convert_var(v: ir.Var) -> logic_pb2.Var:
    return logic_pb2.Var(name=v.name)

def convert_term(t: ir.Term) -> logic_pb2.Term:
    if isinstance(t, ir.Var):
        return logic_pb2.Term(var=convert_var(t))
    else:
        return logic_pb2.Term(constant=convert_constant(t))

def convert_relterm(t: ir.RelTerm) -> logic_pb2.RelTerm:
    if isinstance(t, ir.Specialized):
        val = logic_pb2.SpecializedValue(value=convert_primitive_value(t.value))
        return logic_pb2.RelTerm(specialized_value=val)
    else:
        return logic_pb2.RelTerm(term=convert_term(t))

def convert_relation_id(rid: ir.RelationId) -> logic_pb2.RelationId:
    return logic_pb2.RelationId(id_low=rid.id_low, id_high=rid.id_high)

def convert_fragment_id(fid: ir.FragmentId) -> fragments_pb2.FragmentId:
    return fragments_pb2.FragmentId(id=fid.id)

def convert_attribute(attr: ir.Attribute) -> logic_pb2.Attribute:
    return logic_pb2.Attribute(
        name=attr.name,
        args=[convert_constant(arg) for arg in attr.args]
    )

def convert_abstraction(abst: ir.Abstraction) -> logic_pb2.Abstraction:
    bindings = [logic_pb2.Binding(var=logic_pb2.Var(name=var_tuple[0].name), type=convert_rel_type(var_tuple[1]))
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
            type=convert_rel_type(f.type),
            input=convert_term(f.input),
            result=convert_term(f.result)
        ))
    else:
        raise TypeError(f"Unsupported Formula type: {type(f)}")

def convert_loop_index(li: ir.LoopIndex) -> logic_pb2.LoopIndex:
    return logic_pb2.LoopIndex(name=li.name)

def convert_def(d: ir.Def) -> logic_pb2.Def:
    return logic_pb2.Def(
        name=convert_relation_id(d.name),
        body=convert_abstraction(d.body),
        attrs=[convert_attribute(attr) for attr in d.attrs]
    )

def convert_loop(l: ir.Loop) -> logic_pb2.Loop:
    return logic_pb2.Loop(
        temporal_var=convert_loop_index(l.temporal_var),
        inits=[convert_def(init_def) for init_def in l.inits],
        body=[convert_declaration(decl) for decl in l.body]
    )

def convert_declaration(decl: ir.Declaration) -> logic_pb2.Declaration:
    if isinstance(decl, ir.Def):
        # 'def' is a Python keyword, so we use the same approach as with 'not'
        from typing import Dict, Any
        decl_dict: Dict[str, Any] = {'def': convert_def(decl)}
        return logic_pb2.Declaration(**decl_dict)  # type: ignore
    elif isinstance(decl, ir.Loop):
        return logic_pb2.Declaration(loop=convert_loop(decl))
    else:
        raise TypeError(f"Unsupported Declaration type: {type(decl)}")

def convert_fragment(frag: ir.Fragment) -> fragments_pb2.Fragment:
    return fragments_pb2.Fragment(
        id=convert_fragment_id(frag.id),
        declarations=[convert_declaration(decl) for decl in frag.declarations]
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
    else:
        raise TypeError(f"Unsupported Read type: {type(rt)}")

def convert_epoch(e: ir.Epoch) -> transactions_pb2.Epoch:
    return transactions_pb2.Epoch(
        persistent_writes=[convert_write(w) for w in e.persistent_writes],
        local_writes=[convert_write(w) for w in e.local_writes],
        reads=[convert_read(r) for r in e.reads]
    )

def convert_transaction(t: ir.Transaction) -> transactions_pb2.Transaction:
    return transactions_pb2.Transaction(
        epochs=[convert_epoch(e) for e in t.epochs]
    )

def ir_to_proto(node: ir.LqpNode) -> Union[
    transactions_pb2.Transaction,
    fragments_pb2.Fragment,
    logic_pb2.Declaration,
    logic_pb2.Formula,
    logic_pb2.Term
]:
    if isinstance(node, ir.Transaction):
        return convert_transaction(node)
    elif isinstance(node, ir.Fragment):
        return convert_fragment(node)
    elif isinstance(node, ir.Declaration):
        return convert_declaration(node)
    elif isinstance(node, ir.Formula):
        return convert_formula(node)
    elif isinstance(node, ir.Term):
        return convert_term(node)
    else:
        raise TypeError(f"Unsupported top-level IR node type for conversion: {type(node)}")
