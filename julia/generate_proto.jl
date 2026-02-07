#!/usr/bin/env julia

using Pkg
Pkg.activate("LQPParser")
Pkg.instantiate()

using ProtoBuf

# Generate Julia code from proto files
proto_dir = "../proto"
output_dir = "LQPParser/src"

protojl(
    [
        "relationalai/lqp/v1/logic.proto",
        "relationalai/lqp/v1/fragments.proto",
        "relationalai/lqp/v1/transactions.proto",
    ],
    proto_dir,
    output_dir;
    add_kwarg_constructors=true,
)

println("Generated protobuf code in $output_dir")
