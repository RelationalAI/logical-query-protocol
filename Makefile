# Makefile for the Logical Query Protocol (LQP)
#
# Usage:
#   make              Build protobuf bindings and regenerate all parsers.
#   make build        Lint, check breaking changes, and generate protobuf code.
#   make parsers      Regenerate Python and Julia parsers from the grammar.
#   make parser-X     Regenerate a single parser (X = python, julia).
#   make force-parsers      Force-regenerate both parsers.
#   make force-parser-X     Force-regenerate a single parser.
#   make test         Run tests for all languages.
#   make test-X       Run tests for one language (X = python, julia).
#   make clean        Remove temporary generated files.
#
# Prerequisites: buf, python (with lqp[test] installed), julia.

PROTO_DIR := proto
PROTO_FILES := \
	$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto

GRAMMAR := python-tools/src/meta/grammar.y

# Generated protobuf outputs
PY_PROTO_DIR := python-tools/src/lqp/proto/v1
JL_PROTO_DIR := julia/LQPParser/src/relationalai/lqp/v1

# Generated parser outputs
PY_PARSER := python-tools/src/lqp/generated_parser.py
JL_PARSER := julia/LQPParser/src/parser.jl

# Parser templates
PY_TEMPLATE := python-tools/src/meta/templates/parser.py.template
JL_TEMPLATE := python-tools/src/meta/templates/parser.jl.template

META_CLI := cd python-tools && PYTHONPATH=src python -m meta.cli
META_PROTO_ARGS := \
	../$(PROTO_DIR)/relationalai/lqp/v1/fragments.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/logic.proto \
	../$(PROTO_DIR)/relationalai/lqp/v1/transactions.proto \
	--grammar src/meta/grammar.y


.PHONY: all build lint breaking protobuf protobuf-py protobuf-julia parsers \
	parser-python parser-julia \
	force-parsers force-parser-python force-parser-julia \
	test test-python test-julia check-python \
	clean

all: build parsers

# ---------- protobuf build (replaces ./build script) ----------

build: lint breaking protobuf

lint:
	buf lint

breaking:
	buf breaking --against ".git#branch=main,subdir=proto"

protobuf: protobuf-py protobuf-julia

protobuf-py: $(PROTO_FILES)
	buf generate
	mkdir -p $(PY_PROTO_DIR)
	cp gen/python/relationalai/lqp/v1/*_pb2.py* $(PY_PROTO_DIR)/
	for file in $(PY_PROTO_DIR)/*_pb2.py*; do \
		sed 's/from relationalai\.lqp\.v1/from lqp\.proto\.v1/g' "$$file" > "$$file.tmp" && \
		mv "$$file.tmp" "$$file"; \
		sed 's/import relationalai\.lqp\.v1/import lqp\.proto\.v1/g' "$$file" > "$$file.tmp" && \
		mv "$$file.tmp" "$$file"; \
	done
	rm -rf gen/python gen/go

protobuf-julia: $(PROTO_FILES)
	cd julia && julia --project=LQPParser generate_proto.jl

# ---------- parser generation ----------

parsers: parser-python parser-julia

parser-python: $(PY_PARSER)
$(PY_PARSER): $(PROTO_FILES) $(GRAMMAR) $(PY_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/generated_parser.py

parser-julia: $(JL_PARSER)
$(JL_PARSER): $(PROTO_FILES) $(GRAMMAR) $(JL_TEMPLATE)
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LQPParser/src/parser.jl

force-parsers: force-parser-python force-parser-julia

force-parser-python:
	$(META_CLI) $(META_PROTO_ARGS) --parser python -o src/lqp/generated_parser.py

force-parser-julia:
	$(META_CLI) $(META_PROTO_ARGS) --parser julia -o ../julia/LQPParser/src/parser.jl

# ---------- testing ----------

test: test-python test-julia

test-python: parser-python check-python
	cd python-tools && python -m pytest

test-julia: parser-julia
	cd julia && julia --project=LQPParser -e 'using Pkg; Pkg.test("LQPParser")'

check-python:
	cd python-tools && pyrefly check

# ---------- cleanup ----------

clean:
	rm -rf gen/python gen/go
