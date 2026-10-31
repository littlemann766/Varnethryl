## HTTP API client for the Varnethryl relay: GET /rooms, GET /health.
## Usage: var r = await NetApi.rooms(self)  -> {ok, worlds:[{code,name,players,capacity}], maxPlayers}
class_name NetApi
extends RefCounted

static func _get_json(parent: Node, path: String, timeout := 10.0) -> Dictionary:
	var net := parent.get_node_or_null("/root/Net")
	var base: String = net.http_url if net else "https://varnethryl-world-server-production.up.railway.app"
	var req := HTTPRequest.new()
	req.timeout = timeout
	parent.add_child(req)
	if req.request(base + path, ["Cache-Control: no-store"]) != OK:
		req.queue_free(); return {"ok": false, "error": "request failed"}
	var res: Array = await req.request_completed
	req.queue_free()
	if res[0] != HTTPRequest.RESULT_SUCCESS or res[1] != 200:
		return {"ok": false, "error": "HTTP %d / result %d" % [res[1], res[0]]}
	var data = JSON.parse_string((res[3] as PackedByteArray).get_string_from_utf8())
	return data if typeof(data) == TYPE_DICTIONARY else {"ok": false, "error": "bad json"}

static func rooms(parent: Node) -> Dictionary: return await _get_json(parent, "/rooms")
static func health(parent: Node) -> Dictionary: return await _get_json(parent, "/health")
