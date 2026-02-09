package test

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	lqp "logical-query-protocol/src"
	pb "logical-query-protocol/src/lqp/v1"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
)

// TestBasicParsing tests simple transaction parsing
func TestBasicParsing(t *testing.T) {
	input := `
(transaction
  (epoch
    (writes)
    (reads)))
`
	result, err := lqp.Parse(input)
	if err != nil {
		t.Fatalf("Failed to parse basic transaction: %v", err)
	}
	if result == nil {
		t.Fatal("Parse returned nil result")
	}
	if len(result.Epochs) != 1 {
		t.Errorf("Expected 1 epoch, got %d", len(result.Epochs))
	}
}

// TestParseLQPFiles parses all LQP files and compares against binary snapshots
func TestParseLQPFiles(t *testing.T) {
	// Get the repository root directory (go up two levels from test directory)
	testDir, err := filepath.Abs(".")
	if err != nil {
		t.Fatalf("Failed to get test directory: %v", err)
	}

	// Go up to the repository root (from go/test to repo root)
	repoRoot := filepath.Join(testDir, "..", "..")

	lqpDir := filepath.Join(repoRoot, "python-tools", "tests", "test_files", "lqp")
	binDir := filepath.Join(repoRoot, "python-tools", "tests", "test_files", "bin")

	// Read all .lqp files
	entries, err := os.ReadDir(lqpDir)
	if err != nil {
		t.Fatalf("Failed to read LQP directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".lqp") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			// Read LQP file
			lqpPath := filepath.Join(lqpDir, entry.Name())
			content, err := os.ReadFile(lqpPath)
			if err != nil {
				t.Fatalf("Failed to read LQP file %s: %v", entry.Name(), err)
			}

			// Parse the LQP file
			result, err := lqp.Parse(string(content))
			if err != nil {
				t.Fatalf("Failed to parse LQP file %s: %v", entry.Name(), err)
			}
			if result == nil {
				t.Fatalf("Parse returned nil for %s", entry.Name())
			}

			// Serialize to binary
			generatedBinary, err := proto.Marshal(result)
			if err != nil {
				t.Fatalf("Failed to marshal parsed result for %s: %v", entry.Name(), err)
			}

			// Read expected binary
			binName := strings.Replace(entry.Name(), ".lqp", ".bin", 1)
			binPath := filepath.Join(binDir, binName)
			expectedBinary, err := os.ReadFile(binPath)
			if err != nil {
				t.Logf("Warning: No binary snapshot found for %s, skipping binary comparison", entry.Name())
				return
			}

			// Unmarshal both and compare with normalized debug info
			goTxn := &pb.Transaction{}
			if err := proto.Unmarshal(generatedBinary, goTxn); err != nil {
				t.Fatalf("Failed to unmarshal Go result for %s: %v", entry.Name(), err)
			}
			pyTxn := &pb.Transaction{}
			if err := proto.Unmarshal(expectedBinary, pyTxn); err != nil {
				t.Fatalf("Failed to unmarshal expected binary for %s: %v", entry.Name(), err)
			}

			sortDebugInfo(goTxn)
			sortDebugInfo(pyTxn)

			if !proto.Equal(goTxn, pyTxn) {
				goStr := lqp.ProgramToStr(goTxn)
				pyStr := lqp.ProgramToStr(pyTxn)
				t.Errorf("Parsed result does not match expected for %s\n\nGo:\n%s\n\nPython:\n%s",
					entry.Name(), goStr, pyStr)
			}
		})
	}
}

// sortDebugInfo walks the proto message tree and sorts all DebugInfo
// entries by (IdHigh, IdLow) so comparison is independent of map iteration order.
func sortDebugInfo(msg proto.Message) {
	sortDebugInfoReflect(msg.ProtoReflect())
}

func sortDebugInfoReflect(m protoreflect.Message) {
	m.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		switch {
		case fd.IsList():
			list := v.List()
			if fd.Message() != nil {
				for i := 0; i < list.Len(); i++ {
					sortDebugInfoReflect(list.Get(i).Message())
				}
			}
		case fd.Message() != nil:
			sortDebugInfoReflect(v.Message())
		}
		return true
	})

	// If this message is a DebugInfo, sort its parallel arrays
	if m.Descriptor().FullName() == "relationalai.lqp.v1.DebugInfo" {
		sortDebugInfoFields(m)
	}
}

func sortDebugInfoFields(m protoreflect.Message) {
	di, ok := m.Interface().(*pb.DebugInfo)
	if !ok || len(di.Ids) <= 1 {
		return
	}
	n := len(di.Ids)
	idx := make([]int, n)
	for i := range idx {
		idx[i] = i
	}
	sort.Slice(idx, func(a, b int) bool {
		ia, ib := di.Ids[idx[a]], di.Ids[idx[b]]
		if ia.IdHigh != ib.IdHigh {
			return ia.IdHigh < ib.IdHigh
		}
		return ia.IdLow < ib.IdLow
	})
	sortedIds := make([]*pb.RelationId, n)
	sortedNames := make([]string, n)
	for i, j := range idx {
		sortedIds[i] = di.Ids[j]
		sortedNames[i] = di.OrigNames[j]
	}
	di.Ids = sortedIds
	di.OrigNames = sortedNames
}
