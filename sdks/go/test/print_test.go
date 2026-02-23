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

func repoRoot(t *testing.T) string {
	t.Helper()
	testDir, err := filepath.Abs(".")
	if err != nil {
		t.Fatalf("Failed to get test directory: %v", err)
	}
	return filepath.Join(testDir, "..", "..", "..")
}

// TestPrintBinaryFiles reads binary files, prints them, and compares with expected output.
func TestPrintBinaryFiles(t *testing.T) {
	root := repoRoot(t)
	binDir := filepath.Join(root, "tests", "bin")
	expectedDir := filepath.Join(root, "tests", "pretty")

	entries, err := os.ReadDir(binDir)
	if err != nil {
		t.Fatalf("Failed to read bin directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".bin") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			data, err := os.ReadFile(filepath.Join(binDir, entry.Name()))
			if err != nil {
				t.Fatalf("Failed to read binary file %s: %v", entry.Name(), err)
			}

			transaction := &pb.Transaction{}
			if err := proto.Unmarshal(data, transaction); err != nil {
				t.Fatalf("Failed to unmarshal binary file %s: %v", entry.Name(), err)
			}

			printed := lqp.ProgramToStr(transaction)

			expectedName := strings.Replace(entry.Name(), ".bin", ".lqp", 1)
			expectedData, err := os.ReadFile(filepath.Join(expectedDir, expectedName))
			if err != nil {
				t.Fatalf("Failed to read expected output file %s: %v", expectedName, err)
			}

			if printed != string(expectedData) {
				t.Errorf("Output mismatch for %s\n\nExpected:\n%s\n\nGot:\n%s", entry.Name(), expectedData, printed)
			}
		})
	}
}

// TestPrintDebugBinaryFiles reads binary files, debug-prints them, and compares with expected output.
func TestPrintDebugBinaryFiles(t *testing.T) {
	root := repoRoot(t)
	binDir := filepath.Join(root, "tests", "bin")
	expectedDir := filepath.Join(root, "tests", "pretty_debug")

	entries, err := os.ReadDir(binDir)
	if err != nil {
		t.Fatalf("Failed to read bin directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".bin") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			data, err := os.ReadFile(filepath.Join(binDir, entry.Name()))
			if err != nil {
				t.Fatalf("Failed to read binary file %s: %v", entry.Name(), err)
			}

			transaction := &pb.Transaction{}
			if err := proto.Unmarshal(data, transaction); err != nil {
				t.Fatalf("Failed to unmarshal binary file %s: %v", entry.Name(), err)
			}

			printed := lqp.ProgramToStrDebug(transaction)

			expectedName := strings.Replace(entry.Name(), ".bin", ".lqp", 1)
			expectedData, err := os.ReadFile(filepath.Join(expectedDir, expectedName))
			if err != nil {
				t.Fatalf("Failed to read expected output file %s: %v", expectedName, err)
			}

			if printed != string(expectedData) {
				t.Errorf("Output mismatch for %s\n\nExpected:\n%s\n\nGot:\n%s", entry.Name(), expectedData, printed)
			}
		})
	}
}


// TestRoundtripLQP verifies parse → pretty → parse → pretty stability for .lqp files.
func TestRoundtripLQP(t *testing.T) {
	root := repoRoot(t)
	lqpDir := filepath.Join(root, "tests", "lqp")

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
				t.Fatalf("Failed to read LQP file: %v", err)
			}

			parsed, err := lqp.Parse(string(content))
			if err != nil {
				t.Fatalf("Failed to parse: %v", err)
			}

			printed := lqp.ProgramToStr(parsed)
			reparsed, err := lqp.Parse(printed)
			if err != nil {
				t.Fatalf("Failed to re-parse pretty output: %v", err)
			}

			reprinted := lqp.ProgramToStr(reparsed)
			if printed != reprinted {
				t.Errorf("Roundtrip mismatch for %s\n\nFirst pretty:\n%s\n\nSecond pretty:\n%s",
					entry.Name(), printed, reprinted)
			}
		})
	}
}

// TestRoundtripBinary verifies binary → pretty → parse → pretty stability for .bin files.
func TestRoundtripBinary(t *testing.T) {
	root := repoRoot(t)
	binDir := filepath.Join(root, "tests", "bin")

	entries, err := os.ReadDir(binDir)
	if err != nil {
		t.Fatalf("Failed to read bin directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".bin") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			data, err := os.ReadFile(filepath.Join(binDir, entry.Name()))
			if err != nil {
				t.Fatalf("Failed to read binary file: %v", err)
			}

			transaction := &pb.Transaction{}
			if err := proto.Unmarshal(data, transaction); err != nil {
				t.Fatalf("Failed to unmarshal: %v", err)
			}

			printed := lqp.ProgramToStr(transaction)
			reparsed, err := lqp.Parse(printed)
			if err != nil {
				t.Fatalf("Failed to re-parse pretty output: %v", err)
			}

			reprinted := lqp.ProgramToStr(reparsed)
			if printed != reprinted {
				t.Errorf("Binary roundtrip mismatch for %s\n\nFirst pretty:\n%s\n\nSecond pretty:\n%s",
					entry.Name(), printed, reprinted)
			}
		})
	}
}
