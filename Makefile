# Makefile for the Logical Query Protocol (LQP)
#
# Usage:
#   make              Build protobuf bindings, parsers, and printers.
#   make protobuf     Lint, check breaking changes, and generate protobuf code.
#   make parsers      Regenerate Python, Julia, and Go parsers from the grammar.
#   make parser-X     Regenerate a single parser (X = python, julia, go).
#   make force-parsers      Force-regenerate all parsers.
#   make force-parser-X     Force-regenerate a single parser.
#   make printers     Regenerate pretty printers from the grammar.
#   make printer-X    Regenerate a single printer (X = python, julia, go).
#   make force-printers     Force-regenerate all printers.
#   make force-printer-X    Force-regenerate a single printer.
#   make test         Run tests for all languages.
#   make test-X       Run tests for one language (X = python, julia, go).
#   make update-snapshots  Regenerate Python snapshot test outputs.
#   make lint-python  Run ruff lint and format checks.
#   make format-python  Auto-format Python code with ruff.
#   make clean        Remove temporary generated files.
#
# Prerequisites: buf, uv (python), julia, go.

PROTO_DIR := proto
PROTO_FILES := \
	$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto

GRAMMAR := meta/src/meta/grammar.y

# Generated protobuf outputs
PY_PROTO_DIR := sdks/python/src/lqp/proto/v1
JL_PROTO_DIR := sdks/julia/LogicalQueryProtocol/src/gen/relationalai/lqp/v1
GO_PROTO_DIR := sdks/go/src/lqp/v1

# Generated parser outputs
PY_PARSER := sdks/python/src/lqp/gen/parser.py
JL_PARSER := sdks/julia/LogicalQueryProtocol/src/parser.jl
GO_PARSER := sdks/go/src/parser.go

# Generated printer outputs
PY_PRINTER := sdks/python/src/lqp/gen/pretty.py
GO_PRINTER := sdks/go/src/pretty.go
JL_PRINTER := sdks/julia/LogicalQueryProtocol/src/pretty.jl

# Parser templates
PY_TEMPLATE := meta/src/meta/templates/parser.py.template
JL_TEMPLATE := meta/src/meta/templates/parser.jl.template
GO_TEMPLATE := meta/src/meta/templates/parser.go.template

# Printer templates
PY_PRINTER_TEMPLATE := meta/src/meta/templates/pretty_printer.py.template
JL_PRINTER_TEMPLATE := meta/src/meta/templates/pretty_printer.jl.template
GO_PRINTER_TEMPLATE := meta/src/meta/templates/pretty_printer.go.template

META_CLI := cd meta && uv run python -m meta.cli
META_PROTO_ARGS := \
	../$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto \
	--grammar src/meta/grammar.y

# Generated protobuf files used to track freshness
PY_PROTO_GENERATED := \
	$(PY_PROTO_DIR)/logic_pb2.py \
	$(PY_PROTO_DIR)/fragments_pb2.py \
	$(PY_PROTO_DIR)/transactions_pb2.py
GO_PROTO_GENERATED := \
	$(GO_PROTO_DIR)/logic.pb.go \
	$(GO_PROTO_DIR)/fragments.pb.go \
	$(GO_PROTO_DIR)/transactions.pb.go
JL_PROTO_GENERATED := \
	$(JL_PROTO_DIR)/logic_pb.jl \
	$(JL_PROTO_DIR)/fragments_pb.jl \
	$(JL_PROTO_DIR)/transactions_pb.jl

.PHONY: all protobuf parsers parser-python parser-julia parser-go \
	force-parsers force-parser-python force-parser-julia force-parser-go \
	printers printer-python printer-julia printer-go \
	force-printers force-printer-python force-printer-julia force-printer-go \
	test test-python update-snapshots test-julia test-go \
	test-meta check-python check-meta lint-meta format-meta \
	lint-python format-python clean

all: protobuf parsers printers

# ---------- protobuf build ----------

protobuf: $(PY_PROTO_GENERATED) $(GO_PROTO_GENERATED) $(JL_PROTO_GENERATED)

# This rule is there to trick a later run of make to not regenerate the protobuf files
touch-proto-generated:
	touch $(PY_PROTO_GENERATED) $(GO_PROTO_GENERATED) $(JL_PROTO_GENERATED)

$(PY_PROTO_GENERATED) $(GO_PROTO_GENERATED): $(PROTO_FILES)
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

$(JL_PROTO_GENERATED): $(PROTO_FILES)
	buf lint
	buf breaking --against ".git#branch=main,subdir=proto"
	cd sdks/julia && julia --project=LogicalQueryProtocol generate_proto.jl

# ---------- parser generation ----------

parsers: parser-python parser-julia parser-go

parser-python: $(PY_PARSER)
$(PY_PARSER): $(PROTO_FILES) $(GRAMMAR) $(PY_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o ../sdks/python/src/lqp/gen/parser.py

parser-julia: $(JL_PARSER)
$(JL_PARSER): $(PROTO_FILES) $(GRAMMAR) $(JL_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../sdks/julia/LogicalQueryProtocol/src/parser.jl

parser-go: $(GO_PARSER)
$(GO_PARSER): $(PROTO_FILES) $(GRAMMAR) $(GO_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../sdks/go/src/parser.go

force-parsers: force-parser-python force-parser-julia force-parser-go

force-parser-python:
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o ../sdks/python/src/lqp/gen/parser.py

force-parser-julia:
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../sdks/julia/LogicalQueryProtocol/src/parser.jl

force-parser-go:
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../sdks/go/src/parser.go

# ---------- printer generation ----------

printers: printer-python printer-julia printer-go

printer-python: $(PY_PRINTER)
$(PY_PRINTER): $(PROTO_FILES) $(GRAMMAR) $(PY_PRINTER_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --printer python -o ../sdks/python/src/lqp/gen/pretty.py

printer-julia: $(JL_PRINTER)
$(JL_PRINTER): $(PROTO_FILES) $(GRAMMAR) $(JL_PRINTER_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --printer julia -o ../sdks/julia/LogicalQueryProtocol/src/pretty.jl

printer-go: $(GO_PRINTER)
$(GO_PRINTER): $(PROTO_FILES) $(GRAMMAR) $(GO_PRINTER_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --printer go -o ../sdks/go/src/pretty.go

force-printers: force-printer-python force-printer-julia force-printer-go

force-printer-python:
	$(META_CLI) $(META_PROTO_ARGS) --printer python -o ../sdks/python/src/lqp/gen/pretty.py

force-printer-julia:
	$(META_CLI) $(META_PROTO_ARGS) --printer julia -o ../sdks/julia/LogicalQueryProtocol/src/pretty.jl

force-printer-go:
	$(META_CLI) $(META_PROTO_ARGS) --printer go -o ../sdks/go/src/pretty.go

# ---------- testing ----------

test: test-meta test-python test-julia test-go

test-python: $(PY_PARSER) $(PY_PROTO_GENERATED) check-python
	cd sdks/python && uv run python -m pytest

update-snapshots: $(PY_PARSER) $(PY_PROTO_GENERATED)
	cd sdks/python && uv run python -m pytest --snapshot-update

test-julia: $(JL_PARSER) $(JL_PROTO_GENERATED)
	cd sdks/julia && julia --project=LogicalQueryProtocol -e 'using Pkg; Pkg.test()'

test-go: $(GO_PARSER) $(GO_PROTO_GENERATED)
	cd sdks/go && go test ./test/...

check-python: lint-python
	cd sdks/python && uv run pyrefly check

lint-python:
	cd sdks/python && uv run ruff check
	cd sdks/python && uv run ruff format --check

format-python:
	cd sdks/python && uv run ruff format

test-meta: check-meta
	cd meta && uv run python -m pytest

check-meta: lint-meta
	cd meta && uv run pyrefly check

lint-meta:
	cd meta && uv run ruff check
	cd meta && uv run ruff format --check

format-meta:
	cd meta && uv run ruff format

# ---------- cleanup ----------

clean:
	rm -rf gen/python gen/go gen
