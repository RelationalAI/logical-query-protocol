package lqp_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	lqp "logical-query-protocol/src"
)

func TestParserSimple(t *testing.T) {
	input := `
;; Simple fragment defining a relation 'person' and using variables correctly
(transaction
  (epoch
    (writes
      (define
        (fragment :frag
          (def :person
            ([name::STRING age::INT] ;; Declare vars in abstraction
             (exists [city::STRING] ;; Declare var in exists
               (and
                 (atom :source name age city) ;; Use declared vars
                 (= age 10) ;; Use declared var and constant
                 (primitive :some_check city)))))))))) ;; Use declared var
`

	reader := strings.NewReader(input)
	result, err := lqp.ParseLQP(reader, "test.lqp")
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// Check that we got a transaction
	txn, ok := result.(*lqp.Transaction)
	if !ok {
		t.Fatalf("Expected *lqp.Transaction, got %T", result)
	}

	// Check that we have one epoch
	if len(txn.Epochs) != 1 {
		t.Fatalf("Expected 1 epoch, got %d", len(txn.Epochs))
	}

	// Check that we have one write
	epoch := txn.Epochs[0]
	if len(epoch.Writes) != 1 {
		t.Fatalf("Expected 1 write, got %d", len(epoch.Writes))
	}

	// Check that the write is a define
	write := epoch.Writes[0]
	define, ok := write.WriteType.(*lqp.Define)
	if !ok {
		t.Fatalf("Expected *lqp.Define, got %T", write.WriteType)
	}

	// Check the fragment
	if string(define.Fragment.Id.Id) != "frag" {
		t.Fatalf("Expected fragment id 'frag', got '%s'", string(define.Fragment.Id.Id))
	}

	// Check that we have one declaration
	if len(define.Fragment.Declarations) != 1 {
		t.Fatalf("Expected 1 declaration, got %d", len(define.Fragment.Declarations))
	}

	// Check that it's a def
	def, ok := define.Fragment.Declarations[0].(*lqp.Def)
	if !ok {
		t.Fatalf("Expected *lqp.Def, got %T", define.Fragment.Declarations[0])
	}

	// Check the abstraction has 2 bindings
	if len(def.Body.Vars) != 2 {
		t.Fatalf("Expected 2 bindings, got %d", len(def.Body.Vars))
	}

	t.Logf("Successfully parsed simple transaction!")
}

func TestParserArithmetic(t *testing.T) {
	input := `
(transaction
  (epoch
    (writes
      (define
        (fragment :f1
          (def :decimal_64 ([plus::(DECIMAL 18 6) minus::(DECIMAL 18 6) mult::(DECIMAL 18 6) div::(DECIMAL 18 6)]
            (exists [a::(DECIMAL 18 6) b::(DECIMAL 18 6)]
              (and
                (relatom :dec_64_a a)
                (relatom :dec_64_b b)
                (+ a b plus)
                (- a b minus)
                (* a b mult)
                (/ a b div))))))))

    (reads
      (output :dec_64 :decimal_64)
      (output :dec_128 :decimal_128))))
`

	reader := strings.NewReader(input)
	result, err := lqp.ParseLQP(reader, "arithmetic.lqp")
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// Check that we got a transaction
	txn, ok := result.(*lqp.Transaction)
	if !ok {
		t.Fatalf("Expected *lqp.Transaction, got %T", result)
	}

	// Check reads
	if len(txn.Epochs[0].Reads) != 2 {
		t.Fatalf("Expected 2 reads, got %d", len(txn.Epochs[0].Reads))
	}

	t.Logf("Successfully parsed arithmetic transaction!")
}

func TestParserFragment(t *testing.T) {
	input := `
(fragment :test_frag
  (def :my_relation
    ([x::INT y::STRING]
     (atom :source x y))))
`

	reader := strings.NewReader(input)
	result, err := lqp.ParseLQP(reader, "fragment.lqp")
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// Check that we got a fragment
	frag, ok := result.(*lqp.Fragment)
	if !ok {
		t.Fatalf("Expected *lqp.Fragment, got %T", result)
	}

	// Check fragment id
	if string(frag.Id.Id) != "test_frag" {
		t.Fatalf("Expected fragment id 'test_frag', got '%s'", string(frag.Id.Id))
	}

	t.Logf("Successfully parsed fragment!")
}

func TestParserValues(t *testing.T) {
	input := `
(transaction
  (epoch
    (writes
      (define
        (fragment :values
          (def :test_values
            ([]
             (add
               (= x "hello")
               (= y 42)
               (= z 3.14)
               (= a true)
               (= b false)
               (= c missing)
               (= d 0xdeadbeef)
               (= e 123i128)))))))))
`

	reader := strings.NewReader(input)
	result, err := lqp.ParseLQP(reader, "values.lqp")
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	txn, ok := result.(*lqp.Transaction)
	if !ok {
		t.Fatalf("Expected *lqp.Transaction, got %T", result)
	}

	t.Logf("Successfully parsed values! Got transaction with %d epochs", len(txn.Epochs))
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
