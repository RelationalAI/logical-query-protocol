package lqp

import (
	"bytes"
)

// MsgToStr pretty-prints a single protobuf message via pprintDispatch
// and returns the output string. Exported for use in tests.
func MsgToStr(msg interface{}) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:                        &buf,
		indentStack:              []int{0},
		column:                   0,
		atLineStart:              true,
		separator:                "\n",
		maxWidth:                 maxWidth,
		computing:                make(map[uintptr]bool),
		memo:                     make(map[uintptr]string),
		debugInfo:                make(map[[2]uint64]string),
		printSymbolicRelationIds: true,
	}
	p.pprintDispatch(msg)
	return p.getOutput()
}
