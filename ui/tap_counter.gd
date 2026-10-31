extends RefCounted
class_name VTapCounter
## Port of cheatboot.js createTapCounter: true on the Nth tap inside the window, then resets.
const TAP_COUNT := 5
const TAP_WINDOW_MS := 2500
var n := TAP_COUNT
var win := TAP_WINDOW_MS
var taps := 0
var first := 0
func _init(count := TAP_COUNT, window_ms := TAP_WINDOW_MS) -> void:
	n = count; win = window_ms
func tap(t: int = Time.get_ticks_msec()) -> bool:
	if taps == 0 or t - first > win:
		taps = 0; first = t
	taps += 1
	if taps >= n:
		taps = 0; return true
	return false
