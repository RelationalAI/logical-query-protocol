package test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	lqp "github.com/RelationalAI/logical-query-protocol/sdks/go/src"
	pb "github.com/RelationalAI/logical-query-protocol/sdks/go/src/lqp/v1"

	"google.golang.org/protobuf/proto"
)

// TestBasicParsing tests simple transaction parsing.
func TestBasicParsing(t *testing.T) {
	input := `
(transaction
  (epoch
    (writes)
    (reads)))
`
	result, _, err := lqp.Parse(input)
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

// TestParseTransaction tests the ParseTransaction entry point.
func TestParseTransaction(t *testing.T) {
	input := `(transaction (epoch (writes) (reads)))`
	result, err := lqp.ParseTransaction(input)
	if err != nil {
		t.Fatalf("Failed to parse transaction: %v", err)
	}
	if result == nil {
		t.Fatal("ParseTransaction returned nil")
	}
	if len(result.Epochs) != 1 {
		t.Errorf("Expected 1 epoch, got %d", len(result.Epochs))
	}
}

// TestParseFragment tests the ParseFragment entry point.
func TestParseFragment(t *testing.T) {
	input := `(fragment :test_frag (def :my_rel ([x::INT] (relatom :my_rel x))))`
	result, err := lqp.ParseFragment(input)
	if err != nil {
		t.Fatalf("Failed to parse fragment: %v", err)
	}
	if result == nil {
		t.Fatal("ParseFragment returned nil")
	}
}

// TestParseDelegatesToParseTransaction verifies Parse and ParseTransaction return equal results.
func TestParseDelegatesToParseTransaction(t *testing.T) {
	input := `(transaction (epoch (writes) (reads)))`
	r1, err := lqp.Parse(input)
	if err != nil {
		t.Fatalf("Parse failed: %v", err)
	}
	r2, err := lqp.ParseTransaction(input)
	if err != nil {
		t.Fatalf("ParseTransaction failed: %v", err)
	}
	if !proto.Equal(r1, r2) {
		t.Error("Parse and ParseTransaction should return equal results")
	}
}

// TestParseFragmentRejectsTransaction verifies ParseFragment rejects transaction input.
func TestParseFragmentRejectsTransaction(t *testing.T) {
	_, err := lqp.ParseFragment(`(transaction (epoch (writes) (reads)))`)
	if err == nil {
		t.Error("ParseFragment should reject transaction input")
	}
}

// TestParseTransactionRejectsFragment verifies ParseTransaction rejects fragment input.
func TestParseTransactionRejectsFragment(t *testing.T) {
	_, err := lqp.ParseTransaction(`(fragment :f (def :r ([x::INT] (relatom :r x))))`)
	if err == nil {
		t.Error("ParseTransaction should reject fragment input")
	}
}

// TestParseLQPFiles parses all LQP files and compares against binary snapshots.
func TestParseLQPFiles(t *testing.T) {
	root := repoRoot(t)
	lqpDir := filepath.Join(root, "tests", "lqp")
	binDir := filepath.Join(root, "tests", "bin")

	entries, err := os.ReadDir(lqpDir)
	if err != nil {
		t.Fatalf("Failed to read LQP directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".lqp") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			content, err := os.ReadFile(filepath.Join(lqpDir, entry.Name()))
			if err != nil {
				t.Fatalf("Failed to read LQP file %s: %v", entry.Name(), err)
			}

			result, _, err := lqp.Parse(string(content))
			if err != nil {
				t.Fatalf("Failed to parse LQP file %s: %v", entry.Name(), err)
			}
			if result == nil {
				t.Fatalf("Parse returned nil for %s", entry.Name())
			}

			generatedBinary, err := proto.Marshal(result)
			if err != nil {
				t.Fatalf("Failed to marshal parsed result for %s: %v", entry.Name(), err)
			}

			binName := strings.Replace(entry.Name(), ".lqp", ".bin", 1)
			expectedBinary, err := os.ReadFile(filepath.Join(binDir, binName))
			if err != nil {
				t.Logf("Warning: No binary snapshot found for %s, skipping binary comparison", entry.Name())
				return
			}

			if string(generatedBinary) != string(expectedBinary) {
				expectedTransaction := &pb.Transaction{}
				if err := proto.Unmarshal(expectedBinary, expectedTransaction); err != nil {
					t.Fatalf("Failed to unmarshal expected binary for %s: %v", entry.Name(), err)
				}

				generatedPretty := lqp.ProgramToStr(result)
				expectedPretty := lqp.ProgramToStr(expectedTransaction)
				if generatedPretty != expectedPretty {
					t.Errorf("Parsed result does not match expected for %s\n\nParsed:\n%s\n\nExpected:\n%s",
						entry.Name(), generatedPretty, expectedPretty)
				}
			}
		})
	}
}
