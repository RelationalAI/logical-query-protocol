package lqp

import "testing"

// TestRelationIdFromString verifies that relation_id_from_string produces
// the same id across all SDKs (Julia, Python, Go).
func TestRelationIdFromString(t *testing.T) {
	p := NewParser([]Token{})
	rid := p.relationIdFromString("my_relation")
	if rid.IdLow != 0xf2fc83ec57cf8fbc {
		t.Errorf("id_low: got 0x%016x, want 0xf2fc83ec57cf8fbc", rid.IdLow)
	}
	if rid.IdHigh != 0x503f7dc862f367b7 {
		t.Errorf("id_high: got 0x%016x, want 0x503f7dc862f367b7", rid.IdHigh)
	}
}
