## Headless round-trip test. Run:
##   godot --headless --path . -s res://net/tests/net_test.gd
## Env VARN_WS_URL / VARN_HTTP_URL pick the server (default: live Railway).
## Uses a random PRIVATE room code so live public worlds never see the bots.
extends SceneTree

var a: Node
var b: Node
var failures := 0
var Script_ := preload("res://net/Net.gd")

func check(cond: bool, label: String) -> void:
	print(("PASS " if cond else "FAIL ") + label)
	if not cond: failures += 1

func wait_until(cond: Callable, secs := 8.0) -> bool:
	var t := 0.0
	while t < secs:
		if cond.call(): return true
		await process_frame
		t += 1.0 / 60.0
		OS.delay_msec(16)
	return false

func mk(name_: String) -> Node:
	var n: Node = Script_.new(); n.name = name_; n.auto_reconnect = false
	root.add_child(n); return n

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var probe: Node = Script_.new(); probe.name = "Net"; root.add_child(probe)
	print("server: ", probe.ws_url)
	var h := await NetApi.health(root); check(h.get("ok", false), "GET /health")
	var r := await NetApi.rooms(root); check(r.get("ok", false) and r.worlds.size() == 3, "GET /rooms lists 3 public worlds")
	var code := "T" + str(randi() % 100000000).pad_zeros(9)
	a = mk("A"); b = mk("B")
	var t0 := Time.get_ticks_msec()
	a.join(code, "GodotA", "game", {"zone": "town", "x": 1.0, "y": 0.0, "z": 2.0, "yaw": 0.0, "hero": "Aldric", "skin": "aldric"})
	check(await wait_until(func(): return a.joined), "A welcomed")
	print("  join round-trip ms: ", Time.get_ticks_msec() - t0)
	var got_join := [false]
	a.peer_joined.connect(func(_p): got_join[0] = true)
	b.join(code, "GodotB", "game")
	check(await wait_until(func(): return b.joined), "B welcomed")
	check(b.peers.has(a.self_id), "B sees A in welcome roster")
	check(await wait_until(func(): return got_join[0]), "A gets 'joined' for B")
	var got := [null]
	b.peer_state.connect(func(p): got[0] = p)
	t0 = Time.get_ticks_msec()
	a.send_state({"zone": "town", "x": 5.5, "y": 0.0, "z": -3.25, "yaw": 1.0, "hero": "Aldric", "skin": "aldric", "moving": true})
	check(await wait_until(func(): return got[0] != null), "state relayed A->B")
	if got[0]: check(is_equal_approx(got[0].x, 5.5) and is_equal_approx(got[0].z, -3.25) and got[0].moving, "state payload intact")
	print("  state relay ms: ", Time.get_ticks_msec() - t0)
	var chat := [null]
	b.chat_received.connect(func(e): chat[0] = e)
	a.send_chat("hello from godot")
	check(await wait_until(func(): return chat[0] != null and chat[0].text == "hello from godot"), "chat relayed")
	var oe := [null]
	a.owner_event.connect(func(m): oe[0] = m)
	a.owner_list()
	check(await wait_until(func(): return oe[0] != null and oe[0].type == "owner-error"), "owner-list refused without auth (rank gate works)")
	var left := [false]
	b.peer_left.connect(func(_id): left[0] = true)
	a.leave()
	check(await wait_until(func(): return left[0]), "B gets 'left' for A")
	b.leave()
	await process_frame
	print("RESULT: ", "ALL PASS" if failures == 0 else "%d FAILED" % failures)
	quit(1 if failures else 0)
