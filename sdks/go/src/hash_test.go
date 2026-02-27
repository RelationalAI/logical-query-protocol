package lqp

import "testing"

// TestRelationIdFromString verifies that relation_id_from_string produces
// the same id across all SDKs (Julia, Python, Go).
func TestRelationIdFromString(t *testing.T) {
	p := NewParser([]Token{})
	rid := p.relationIdFromString("my_relation")
	if rid.IdLow != 0x5d33996702404f85 {
		t.Errorf("id_low: got 0x%016x, want 0x5d33996702404f85", rid.IdLow)
	}
	if rid.IdHigh != 0x3b9af8e72af633f8 {
		t.Errorf("id_high: got 0x%016x, want 0x3b9af8e72af633f8", rid.IdHigh)
	}
}
