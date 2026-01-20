#!/usr/bin/env julia

using Pkg
Pkg.activate("LQPParser.jl")
Pkg.add(name="ProtoBuf", version="1.2.0")
Pkg.instantiate()

using ProtoBuf

# Generate Julia code from proto files
proto_dir = "../proto"
output_dir = "LQPParser.jl/src"

# Generate code for all proto files
# Paths should be relative to proto_dir
protojl(
    [
        "relationalai/lqp/v1/logic.proto",
        "relationalai/lqp/v1/fragments.proto",
        "relationalai/lqp/v1/transactions.proto",
    ],
    proto_dir,
    output_dir
)

println("Generated protobuf code in $output_dir")
