@testitem "Provenance - root transaction" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    @test haskey(provenance, ())
    span = provenance[()]
    @test span.start.offset == 1  # 1-based in Julia
    @test span.start.line == 1
    @test span.start.column == 1
end

@testitem "Provenance - span ordering" setup=[ParserSetup] begin
    input = "(transaction\n  (epoch\n    (writes)\n    (reads)))\n"
    _, provenance = Parser.parse(input)

    for (path, span) in provenance
        @test span.start.offset <= span.stop.offset
        @test span.start.line <= span.stop.line
    end
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
