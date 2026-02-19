# The Logical Query Protocol (LQP)

The LQP connects decision agents to engines for rules-based reasoning over relational
knowledge graphs.

It is intended for direct use by an agent, or as a target for higher-level compilers. Making
it easy to write for humans is not a design goal, however human _readability_ is a priority
for alignment and debugging.

This repository contains the protobuf specification of the protocol in `../proto`. What
follows is a high-level description of the key concepts.

The protocol supports constructs for deriving new relations:

    Declaration := Def(name::RelationId, body::Abstraction, attrs::Attribute[])
                | Algorithm(exports::RelationId[], body::Script)
                | Constraint
                | Data

`Def`s derive a single relation via first-order logic with negation, aggregation, and
recursion.

`Algorithm`s derive one or more relations via arbitrarily nested, iterative computations.

`Constraint`s capture semantic information and relationships between relations. Things like
functional dependencies, inclusion / exclusion, uniqueness, and several others.

`Data` declarations derive one or more relations from external data sources like CSV.

Relations in the LQP are uniquely identified, and statically typed. All types are primitive.
Overloading has to be handled at a higher level.

The full execution graph is broken into _fragments_ that can be defined, redefined, and
undefined independently.

Clients can use an optional `Sync` action to ensure that the state of installed execution
graph on the engine matches what they expect.

LQP clients send `Transaction`s that the engine executes.

    Transaction := Transaction(
        epochs::Epoch[],
        configure::Configure(semantics_version::Int, /* other configuration options */),
        sync::Sync(fragments::FragmentId[]),
    )

    Epoch := Epoch(writes::Write[], reads::Read[])

    Write := Define(fragment::Fragment)
           | Undefine(fragment_id::FragmentId)

    Read := Demand(relation_id::RelationId)
          | Output(name::String, relation_id::RelationId)
          | Export(config::ExportCSVConfig)
          | WhatIf(branch::String, epochs::Epoch[])
          | Abort(name::String, relation_id::RelationId)

Transactions are structured into one or more epochs, which correspond to observable states
of the installed program. This allows users to execute a sequence of steps in a single
transaction. Within an epoch writes execute before reads. Multiple writes or multiple reads
can be performed concurrently and in any order. Of special note are the WhatIf operations,
which allow executing an epoch in a throwaway clone of the runtime state.
