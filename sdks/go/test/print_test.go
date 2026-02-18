package test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	lqp "logical-query-protocol/src"
	pb "logical-query-protocol/src/lqp/v1"

	"google.golang.org/protobuf/proto"
)

// TestPrintBinaryFiles reads binary files, prints them, and compares with expected output
func TestPrintBinaryFiles(t *testing.T) {
	// Get the repository root directory (go up two levels from test directory)
	testDir, err := filepath.Abs(".")
	if err != nil {
		t.Fatalf("Failed to get test directory: %v", err)
	}

	// Go up to the repository root (from sdks/go/test to repo root)
	repoRoot := filepath.Join(testDir, "..", "..", "..")

	binDir := filepath.Join(repoRoot, "tests", "bin")
	expectedDir := filepath.Join(repoRoot, "tests", "pretty")

	// Read all .bin files
	entries, err := os.ReadDir(binDir)
	if err != nil {
		t.Fatalf("Failed to read bin directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".bin") {
			continue
		}

		// Run each test case
		t.Run(entry.Name(), func(t *testing.T) {
			// Read binary file
			binPath := filepath.Join(binDir, entry.Name())
			data, err := os.ReadFile(binPath)
			if err != nil {
				t.Fatalf("Failed to read binary file %s: %v", entry.Name(), err)
			}

			// Deserialize as Transaction
			transaction := &pb.Transaction{}
			err = proto.Unmarshal(data, transaction)
			if err != nil {
				t.Fatalf("Failed to unmarshal binary file %s: %v", entry.Name(), err)
			}

			printed := lqp.ProgramToStr(transaction)

			// Read expected output
			expectedName := strings.Replace(entry.Name(), ".bin", ".lqp", 1)
			expectedPath := filepath.Join(expectedDir, expectedName)
			expectedData, err := os.ReadFile(expectedPath)
			if err != nil {
				t.Fatalf("Failed to read expected output file %s: %v", expectedName, err)
			}
			expected := string(expectedData)

			// Compare
			if printed != expected {
				t.Errorf("Output mismatch for %s\n\nExpected:\n%s\n\nGot:\n%s", entry.Name(), expected, printed)
			}
		})
	}
}
