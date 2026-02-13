# Makefile for the Logical Query Protocol (LQP)
#
# Usage:
#   make              Build protobuf bindings and regenerate all parsers.
#   make protobuf     Lint, check breaking changes, and generate protobuf code.
#   make parsers      Regenerate Python, Julia, and Go parsers from the grammar.
#   make parser-X     Regenerate a single parser (X = python, julia, go).
#   make force-parsers      Force-regenerate all parsers.
#   make force-parser-X     Force-regenerate a single parser.
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

# Generated protobuf outputs
PY_PROTO_DIR := python-tools/src/lqp/proto/v1
JL_PROTO_DIR := julia/LogicalQueryProtocol/src/relationalai/lqp/v1
GO_PROTO_DIR := go/src/lqp/v1

# Generated parser outputs
PY_PARSER := python-tools/src/lqp/gen/parser.py
JL_PARSER := julia/LogicalQueryProtocol/src/parser.jl
GO_PARSER := go/src/parser.go

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
	test test-python test-julia test-go check-python \
	clean

all: build parsers

# ---------- protobuf build (replaces ./build script) ----------

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
	cd julia && julia --project=LogicalQueryProtocol generate_proto.jl

# ---------- parser generation ----------

parsers: parser-python parser-julia parser-go

parser-python: $(PY_PARSER)
$(PY_PARSER): $(PROTO_FILES) $(GRAMMAR) $(PY_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/gen/parser.py

parser-julia: $(JL_PARSER)
$(JL_PARSER): $(PROTO_FILES) $(GRAMMAR) $(JL_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LogicalQueryProtocol/src/parser.jl

parser-go: $(GO_PARSER)
$(GO_PARSER): $(PROTO_FILES) $(GRAMMAR) $(GO_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../go/src/parser.go

force-parsers: force-parser-python force-parser-julia force-parser-go

force-parser-python:
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/gen/parser.py

force-parser-julia:
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LogicalQueryProtocol/src/parser.jl

force-parser-go:
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../go/src/parser.go

# ---------- testing ----------

test: test-python test-julia test-go

test-python: $(PY_PARSER) $(PY_PROTO_GENERATED) check-python
	cd python-tools && python -m pytest

test-julia: $(JL_PARSER) $(JL_PROTO_GENERATED)
	cd julia && julia --project=LogicalQueryProtocol -e 'using Pkg; Pkg.test()'

test-go: $(GO_PARSER) $(GO_PROTO_GENERATED)
	cd go && go test ./test/...

check-python:
	cd python-tools && pyrefly check

# ---------- cleanup ----------

clean:
	rm -rf gen/python gen/go
