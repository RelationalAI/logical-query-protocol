# Makefile for the Logical Query Protocol (LQP)
#
# Usage:
#   make              Build protobuf bindings and regenerate all parsers.
#   make build        Lint, check breaking changes, and generate protobuf code.
#   make parsers      Regenerate Python, Go, and Julia parsers from the grammar.
#   make parser-X     Regenerate a single parser (X = python, go, julia).
#   make test         Run tests for all three languages.
#   make test-X       Run tests for one language (X = python, go, julia).
#   make clean        Remove temporary generated files.
#
# Prerequisites: buf, python (with lqp[test] installed), go, julia.

PROTO_DIR := proto
PROTO_FILES := \
	$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto

GRAMMAR := python-tools/src/meta/grammar.y

# Generated protobuf outputs
PY_PROTO_DIR := python-tools/src/lqp/proto/v1
GO_PROTO_DIR := go/src/lqp/v1

# Generated parser outputs
PY_PARSER := python-tools/src/lqp/generated_parser.py
GO_PARSER := go/src/parser.go
JULIA_PARSER := julia/LQPParser/src/parser.jl

META_CLI := cd python-tools && python -m meta.cli
META_PROTO_ARGS := \
	../$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto \
	--grammar src/meta/grammar.y

.PHONY: all build lint breaking protobuf parsers \
	parser-python parser-go parser-julia \
	test test-python test-go test-julia \
	clean

all: build parsers

# ---------- protobuf build (replaces ./build script) ----------

build: lint breaking protobuf

lint:
	buf lint

breaking:
	buf breaking --against ".git#branch=main,subdir=proto"

protobuf: $(PROTO_FILES)
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
	cp -r gen/go/relationalai/lqp/v1/*.go $(GO_PROTO_DIR)/
	rm -rf gen/python gen/go

# ---------- parser generation ----------

parsers: parser-python parser-go parser-julia

parser-python: $(PY_PARSER)
$(PY_PARSER): $(PROTO_FILES) $(GRAMMAR)
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/generated_parser.py

parser-go: $(GO_PARSER)
$(GO_PARSER): $(PROTO_FILES) $(GRAMMAR)
	$(META_CLI) $(META_PROTO_ARGS) --parser go -o ../go/src/parser.go

parser-julia: $(JULIA_PARSER)
$(JULIA_PARSER): $(PROTO_FILES) $(GRAMMAR)
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LQPParser/src/parser.jl

# ---------- testing ----------

test: test-python test-go test-julia

test-python:
	cd python-tools && python -m pytest

test-go:
	cd go && go test -v ./test/...

test-julia:
	cd julia && julia --project=LQPParser -e 'using Pkg; Pkg.test("LQPParser")'

# ---------- cleanup ----------

clean:
	rm -rf gen/python gen/go
