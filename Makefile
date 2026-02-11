# Makefile for the Logical Query Protocol (LQP)
#
# Usage:
#   make              Build protobuf bindings and regenerate all parsers.
#   make protobuf     Lint, check breaking changes, and generate protobuf code.
#   make parsers      Regenerate Python, Julia, and Go parsers from the grammar.
#   make parser-X     Regenerate a single parser (X = python, julia, go).
#   make force-parsers      Force-regenerate all parsers.
#   make force-parser-X     Force-regenerate a single parser.
#   make printers     Regenerate pretty printers from the grammar.
#   make printer-X    Regenerate a single printer (X = python, go, julia).
#   make test         Run tests for all languages.
#   make test-X       Run tests for one language (X = python, julia, go).
#   make clean        Remove temporary generated files.
#
# Prerequisites: buf, python (with lqp[test] installed), julia, go.

PROTO_DIR := proto
PROTO_FILES := \
	$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto

GRAMMAR := python-tools/src/meta/grammar.y

# Generated protobuf output directories
PY_PROTO_DIR := python-tools/src/lqp/proto/v1
JL_PROTO_DIR := julia/LQPParser/src/relationalai/lqp/v1
GO_PROTO_DIR := go/src/lqp/v1

# Representative generated protobuf files (used as make targets)
PY_GO_PROTO_GEN := $(PY_PROTO_DIR)/logic_pb2.py
JL_PROTO_GEN := $(JL_PROTO_DIR)/logic_pb.jl

# Generated parser outputs
PY_PARSER := python-tools/src/lqp/gen/parser.py
JL_PARSER := julia/LQPParser/src/parser.jl
GO_PARSER := go/src/parser.go

# Generated pretty printer outputs
PY_PRINTER := python-tools/src/lqp/gen/pretty.py
JL_PRINTER := julia/LQPParser/src/pretty_printer.jl
GO_PRINTER := go/src/pretty_printer.go

# Parser templates
PY_TEMPLATE := python-tools/src/meta/templates/parser.py.template
JL_TEMPLATE := python-tools/src/meta/templates/parser.jl.template
GO_TEMPLATE := python-tools/src/meta/templates/parser.go.template

META_CLI := cd python-tools && PYTHONPATH=src python -m meta.cli
META_PROTO_ARGS := \
	../$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto \
	--grammar src/meta/grammar.y


.PHONY: all build protobuf protobuf-lint protobuf-py-go protobuf-julia \
	parsers parser-python parser-julia parser-go \
	force-parsers force-parser-python force-parser-julia force-parser-go \
	printers printer-python printer-julia printer-go \
	force-printers force-printer-python force-printer-julia force-printer-go \
	test test-python test-julia test-go check-python \
	clean

all: build parsers printers

# ---------- protobuf build (replaces ./build script) ----------

protobuf-lint: $(PROTO_FILES)
	buf lint
	buf breaking --against ".git#branch=main,subdir=proto"

# Convenience phony targets
protobuf: $(PY_GO_PROTO_GEN) $(JL_PROTO_GEN)
protobuf-py-go: $(PY_GO_PROTO_GEN)
protobuf-julia: $(JL_PROTO_GEN)

# Only regenerate when .proto files are newer than the generated output
$(PY_GO_PROTO_GEN): $(PROTO_FILES)
	buf lint
	buf breaking --against ".git#branch=main,subdir=proto"
	buf generate
	mkdir -p $(PY_PROTO_DIR)
	cp gen/python/relationalai/lqp/v1/*_pb2.py* $(PY_PROTO_DIR)/
	for file in $(PY_PROTO_DIR)/*_pb2.py*; do \
		sed 's/from relationalai\.lqp\.v1/from lqp\.proto\.v1/g' "$$file" > "$$file.tmp" && \
		mv "$$file.tmp" "$$file"; \
		sed 's/import relationalai\.lqp\.v1/import lqp\.proto\.v1/g' "$$file" > "$$file.tmp" && \
		mv "$$file.tmp" "$$file"; \
	done
	mkdir -p $(GO_PROTO_DIR)
	cp gen/go/relationalai/lqp/v1/*.pb.go $(GO_PROTO_DIR)/
	rm -rf gen/python gen/go

$(JL_PROTO_GEN): $(PROTO_FILES)
	buf lint
	buf breaking --against ".git#branch=main,subdir=proto"
	cd julia && julia --project=LQPParser generate_proto.jl

# ---------- parser generation ----------

parsers: parser-python parser-julia parser-go

parser-python: $(PY_PARSER)
$(PY_PARSER): $(PY_GO_PROTO_GEN) $(GRAMMAR) $(PY_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/gen/parser.py

parser-julia: $(JL_PARSER)
$(JL_PARSER): $(JL_PROTO_GEN) $(GRAMMAR) $(JL_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LQPParser/src/parser.jl

parser-go: $(GO_PARSER)
$(GO_PARSER): $(PY_GO_PROTO_GEN) $(GRAMMAR) $(GO_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../go/src/parser.go

force-parsers: force-parser-python force-parser-julia force-parser-go

force-parser-python: $(PY_GO_PROTO_GEN)
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/gen/parser.py

force-parser-julia: $(JL_PROTO_GEN)
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LQPParser/src/parser.jl

force-parser-go: $(PY_GO_PROTO_GEN)
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../go/src/parser.go

# ---------- pretty printer generation ----------

printers: printer-python printer-julia printer-go

printer-python: $(PY_PRINTER)
$(PY_PRINTER): $(PY_GO_PROTO_GEN) $(GRAMMAR)
	$(META_CLI) $(META_PROTO_ARGS) --printer python -o src/lqp/gen/pretty.py

printer-julia: $(JL_PROTO_GEN)
	@echo "Pretty printer generation for Julia is not yet implemented."

printer-go: $(PY_GO_PROTO_GEN)
	@echo "Pretty printer generation for Go is not yet implemented."

force-printers: force-printer-python force-printer-julia force-printer-go

force-printer-python: $(PY_GO_PROTO_GEN)
	$(META_CLI) $(META_PROTO_ARGS) --printer python -o src/lqp/gen/pretty.py

force-printer-julia: $(JL_PROTO_GEN)
	@echo "Pretty printer generation for Julia is not yet implemented."

force-printer-go: $(PY_GO_PROTO_GEN)
	@echo "Pretty printer generation for Go is not yet implemented."

# ---------- testing ----------

test: test-python test-julia test-go

test-python: parser-python check-python
	cd python-tools && python -m pytest

test-julia: parser-julia
	cd julia && julia --project=LQPParser -e 'using Pkg; Pkg.test("LQPParser")'

test-go: parser-go
	cd go && go test ./test/...

check-python:
	cd python-tools && pyrefly check

# ---------- cleanup ----------

clean:
	rm -rf gen/python gen/go
