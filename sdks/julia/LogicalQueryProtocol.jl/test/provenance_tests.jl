@testitem "Provenance - root transaction" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    @test haskey(provenance, ())
    span = provenance[()]
    @test span.start.offset == 1  # 1-based in Julia
    @test span.start.line == 1
    @test span.start.column == 1
end

@testitem "Provenance - epoch path" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    # epochs = field 1, index 0
    key = (1, 0)
    @test haskey(provenance, key)
    span = provenance[key]
    @test span.start.line == 2
end

@testitem "Provenance - writes path" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    # epochs[0].writes = field 1 within Epoch
    key = (1, 0, 1)
    @test haskey(provenance, key)
    span = provenance[key]
    @test span.start.line == 3
end

@testitem "Provenance - reads path" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    # epochs[0].reads = field 2 within Epoch
    key = (1, 0, 2)
    @test haskey(provenance, key)
    span = provenance[key]
    @test span.start.line == 4
end

@testitem "Provenance - span covers correct text" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    # Root starts at offset 1 (1-based in Julia)
    root_span = provenance[()]
    @test root_span.start.offset == 1

    # Epoch span starts at '(' of '(epoch'
    epoch_span = provenance[(1, 0)]
    text_at_epoch = input[epoch_span.start.offset:end]
    @test startswith(text_at_epoch, "(epoch")
end

@testitem "Provenance - span ordering" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    for (path, span) in provenance
        @test span.start.offset <= span.stop.offset
        @test span.start.line <= span.stop.line
    end
end

@testitem "Provenance - multiple epochs" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads))\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    @test haskey(provenance, (1, 0))
    @test haskey(provenance, (1, 1))

    # First epoch starts before second
    @test provenance[(1, 0)].start.offset < provenance[(1, 1)].start.offset
end

@testitem "Provenance - Location type" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    root_span = provenance[()]
    loc = root_span.start
    @test loc isa Location
    @test loc.line isa Int
    @test loc.column isa Int
    @test loc.offset isa Int
end

@testitem "Provenance - Span type" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    root_span = provenance[()]
    @test root_span isa Span
    @test root_span.start isa Location
    @test root_span.stop isa Location
end
