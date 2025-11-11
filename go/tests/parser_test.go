package lqp_test

import (
	"bytes"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	lqp "logical-query-protocol/src"
)

// assertLqpNodesEqual recursively compares two LQP nodes for structural equality.
// It skips Meta and debug fields, similar to the Python implementation.
func assertLqpNodesEqual(t *testing.T, obj1, obj2 interface{}) {
	t.Helper()

	// Handle nil cases
	if obj1 == nil && obj2 == nil {
		return
	}
	if obj1 == nil || obj2 == nil {
		t.Errorf("One value is nil: %v vs %v", obj1, obj2)
		return
	}

	v1 := reflect.ValueOf(obj1)
	v2 := reflect.ValueOf(obj2)

	// Handle different types
	if v1.Type() != v2.Type() {
		t.Errorf("Types differ: %T vs %T", obj1, obj2)
		return
	}

	// Handle pointers - dereference and compare
	if v1.Kind() == reflect.Ptr {
		if v1.IsNil() && v2.IsNil() {
			return
		}
		if v1.IsNil() || v2.IsNil() {
			t.Errorf("One pointer is nil: %v vs %v", obj1, obj2)
			return
		}
		assertLqpNodesEqual(t, v1.Elem().Interface(), v2.Elem().Interface())
		return
	}

	// Handle slices
	if v1.Kind() == reflect.Slice {
		if v1.Len() != v2.Len() {
			t.Errorf("Slice lengths differ: %d vs %d", v1.Len(), v2.Len())
			return
		}
		for i := 0; i < v1.Len(); i++ {
			assertLqpNodesEqual(t, v1.Index(i).Interface(), v2.Index(i).Interface())
		}
		return
	}

	// Handle maps
	if v1.Kind() == reflect.Map {
		if v1.Len() != v2.Len() {
			t.Errorf("Map lengths differ: %d vs %d", v1.Len(), v2.Len())
			return
		}
		for _, key := range v1.MapKeys() {
			val1 := v1.MapIndex(key)
			val2 := v2.MapIndex(key)
			if !val2.IsValid() {
				t.Errorf("Key %v missing in second map", key.Interface())
				return
			}
			assertLqpNodesEqual(t, val1.Interface(), val2.Interface())
		}
		return
	}

	// Handle floats with NaN special case
	if v1.Kind() == reflect.Float64 || v1.Kind() == reflect.Float32 {
		f1 := v1.Float()
		f2 := v2.Float()
		if math.IsNaN(f1) && math.IsNaN(f2) {
			return
		}
		if f1 != f2 {
			t.Errorf("Float values differ: %v vs %v", f1, f2)
		}
		return
	}

	// Handle structs (including LqpNode types)
	if v1.Kind() == reflect.Struct {
		typ := v1.Type()

		// Special case for ExportCSVConfig - weak comparison (only compare non-nil fields)
		if typ.Name() == "ExportCSVConfig" {
			for i := 0; i < typ.NumField(); i++ {
				field := typ.Field(i)
				fieldName := field.Name

				// Skip Meta and debug fields
				if fieldName == "Meta" || strings.HasPrefix(fieldName, "Debug") {
					continue
				}

				field1 := v1.Field(i)
				field2 := v2.Field(i)

				// Only compare if both values are not nil (for pointer fields)
				if field1.Kind() == reflect.Ptr {
					if !field1.IsNil() && !field2.IsNil() {
						assertLqpNodesEqual(t, field1.Interface(), field2.Interface())
					}
				} else {
					assertLqpNodesEqual(t, field1.Interface(), field2.Interface())
				}
			}
			return
		}

		// Regular struct comparison
		for i := 0; i < typ.NumField(); i++ {
			field := typ.Field(i)
			fieldName := field.Name

			// Skip Meta and debug fields
			if fieldName == "Meta" || strings.HasPrefix(fieldName, "Debug") {
				continue
			}

			field1 := v1.Field(i)
			field2 := v2.Field(i)

			// Skip unexported fields
			if !field1.CanInterface() {
				continue
			}

			assertLqpNodesEqual(t, field1.Interface(), field2.Interface())
		}
		return
	}

	// For primitive types and other values, use direct comparison
	if !reflect.DeepEqual(obj1, obj2) {
		t.Errorf("Values differ: %v vs %v", obj1, obj2)
	}
}

func TestParseAllLQPFiles(t *testing.T) {
	// Parse all .lqp files in the lqp directory
	files, err := filepath.Glob("lqp/*.lqp")
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

func TestRoundTrip(t *testing.T) {
	// Create pretty directory if it doesn't exist
	if err := os.MkdirAll("pretty", 0755); err != nil {
		t.Fatalf("Failed to create pretty directory: %v", err)
	}

	// Get all LQP files from lqp/
	files, err := filepath.Glob("lqp/*.lqp")
	if err != nil {
		t.Fatalf("Failed to find LQP files: %v", err)
	}

	if len(files) == 0 {
		t.Skip("No LQP files found in lqp/")
	}

	for _, file := range files {
		basename := filepath.Base(file)
		t.Run(basename, func(t *testing.T) {
			// Read original file
			content, err := os.ReadFile(file)
			if err != nil {
				t.Fatalf("Failed to read %s: %v", file, err)
			}

			// Parse it
			p := lqp.NewParser(bytes.NewReader(content), file)
			node, err := p.Parse()
			if err != nil {
				t.Fatalf("Failed to parse %s: %v", file, err)
			}

			// Print it back using PrettyConfig
			options := make(map[string]bool)
			for k, v := range lqp.UglyConfig {
				options[k] = v
			}
			options["print_names"] = true
			options["print_debug"] = false
			result := lqp.ToString(node, options)

			// Write the printed output to pretty/
			prettyFile := filepath.Join("pretty", basename)
			if err := os.WriteFile(prettyFile, []byte(result), 0644); err != nil {
				t.Fatalf("Failed to write %s: %v", prettyFile, err)
			}

			// Parse the printed result to verify round-trip correctness
			p2 := lqp.NewParser(strings.NewReader(result), prettyFile)
			node2, err := p2.Parse()
			if err != nil {
				t.Fatalf("Failed to re-parse printed output for %s: %v\nPrinted output written to: %s", file, err, prettyFile)
			}

			// Both parses succeeded - the structures should be equivalent
			t.Logf("✓ Round-trip successful: %s -> %s (original=%d bytes, printed=%d bytes)",
				file, prettyFile, len(content), len(result))

			// Compare the two parsed AST structures for equality
			assertLqpNodesEqual(t, node2, node)
		})
	}
}
