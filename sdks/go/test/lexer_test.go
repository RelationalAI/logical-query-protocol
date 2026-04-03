package test

import (
	"testing"

	lqp "github.com/RelationalAI/logical-query-protocol/sdks/go/src"
)

// TestSymbolLexerRegex verifies that the SYMBOL regex treats hyphen as a literal
// character and does not accidentally include characters like $, %, etc.
func TestSymbolLexerRegex(t *testing.T) {
	t.Run("hyphenated symbol", func(t *testing.T) {
		// A hyphenated relation name should parse without error.
		input := `(fragment :test (def :my-rel ([x::INT] (relatom :my-rel x))))`
		result, _, err := lqp.ParseFragment(input)
		if err != nil {
			t.Fatalf("Failed to parse hyphenated symbol: %v", err)
		}
		if result == nil {
			t.Fatal("ParseFragment returned nil")
		}
	})

	t.Run("symbol with hash and slash", func(t *testing.T) {
		input := `(fragment :test (def :base/#output ([x::INT] (relatom :base/#output x))))`
		result, _, err := lqp.ParseFragment(input)
		if err != nil {
			t.Fatalf("Failed to parse symbol with hash and slash: %v", err)
		}
		if result == nil {
			t.Fatal("ParseFragment returned nil")
		}
	})

	t.Run("dollar terminates symbol", func(t *testing.T) {
		// '$' is not a valid SYMBOL character, so this should fail to parse.
		input := `(fragment :test (def :foo$bar ([x::INT] (relatom :foo$bar x))))`
		_, _, err := lqp.ParseFragment(input)
		if err == nil {
			t.Error("Expected parse error for symbol containing '$'")
		}
	})
}
