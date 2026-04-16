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
           | Context(relations::RelationId[])
           | Snapshot(mappings::SnapshotMapping[], prefix::String[])

    Read := Demand(relation_id::RelationId)
          | Output(name::String, relation_id::RelationId)
          | Export(config::ExportConfig)
          | WhatIf(branch::String, epoch::Epoch)
          | Abort(name::String, relation_id::RelationId)

Transactions are structured into one or more epochs, which correspond to observable states
of the installed program. This allows users to execute a sequence of steps in a single
transaction. Within an epoch writes execute before reads. Multiple writes or multiple reads
can be performed concurrently and in any order. Of special note are the `WhatIf` operations,
which allow executing an epoch in a throwaway clone of the runtime state.

## Execution Model

Transaction execution proceeds in two passes. First, the _simulator_ runs the transaction
against a transient copy of the runtime state to validate it and minimize it (e.g. dropping
writes whose effects are clobbered by later writes). Then the _driver_ executes the
validated, minimized transaction against the actual runtime. If the simulator detects invalid
state at any point, the transaction is aborted and errors are returned.

## Write Operations

`Define` installs a fragment and its declarations into the execution graph. `Undefine`
removes a fragment. `Context` declares which relations should be jointly optimized — more
context gives the optimizer more reuse opportunities but increases planning time. `Snapshot`
materializes derived relations into durable EDB (base) relations, associating new relation
values with stable identities over time.

## Read Operations

`Demand` triggers computation of a relation without returning its contents — useful for
warming caches. `Output` computes and returns a relation's contents under a human-readable
name. `Export` writes data to external storage (CSV or Iceberg). `WhatIf` runs a speculative
epoch on a transient fork; writes don't persist, reads observe the modified state. `Abort`
enforces integrity constraints: the transaction fails if the referenced relation is non-empty.

## Types

All types are primitive and aligned with the Apache Iceberg type system. The engine uses
type information for equality, ordering, promotion, and algebraic properties of operations.
Overloading must be handled by higher-level compilers. See the `Type` message in
`logic.proto` for the full list.

## External Data

`Data` declarations describe external sources (CSV, Iceberg, BeTree) without eagerly
ingesting them — data is loaded lazily when first demanded. `EDB` declares durable
engine-managed base relations (the result of `Snapshot` operations). `CSVData` and
`IcebergData` describe how to read from those respective formats, with column-to-relation
mappings via `GNFColumn`.

## Protobuf Specification

The proto files in `../proto/relationalai/lqp/v1/` are the authoritative specification:

- `logic.proto` — Declarations, formulas, types, values, and external data sources
- `fragments.proto` — Content-addressable compilation units and debug info
- `transactions.proto` — Transaction structure, write/read operations, and export config
