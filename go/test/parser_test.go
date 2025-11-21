package lqp_test

import (
	"os"
	"path/filepath"
	"testing"

	lqp "logical-query-protocol/src"
)

func TestParseAllLQPFiles(t *testing.T) {
	pythonLQPDir := "../../python-tools/tests/test_files/lqp"
	files, err := filepath.Glob(filepath.Join(pythonLQPDir, "*.lqp"))
	if err != nil {
		t.Fatalf("Failed to find lqp files: %v", err)
	}

	if len(files) == 0 {
		t.Skip("No .lqp files found in lqp/ directory")
	}

	passed := 0
	failed := 0
	var failedFiles []string

	for _, file := range files {
		basename := filepath.Base(file)
		t.Run(basename, func(t *testing.T) {
			f, err := os.Open(file)
			if err != nil {
				t.Errorf("Failed to open file: %v", err)
				failed++
				failedFiles = append(failedFiles, basename)
				return
			}
			defer f.Close()

			_, err = lqp.ParseLQP(f, file)
			if err != nil {
				t.Errorf("Parse error: %v", err)
				failed++
				failedFiles = append(failedFiles, basename)
			} else {
				t.Logf("✓ Successfully parsed %s", basename)
				passed++
			}
		})
	}

	t.Logf("\n========================================")
	t.Logf("Results: %d/%d files parsed successfully (%.1f%%)",
		passed, len(files), float64(passed)*100/float64(len(files)))

	if len(failedFiles) > 0 {
		t.Logf("\nFailed files:")
		for _, f := range failedFiles {
			t.Logf("  - %s", f)
		}
	}
}
