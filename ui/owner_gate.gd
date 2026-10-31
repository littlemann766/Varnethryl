extends RefCounted
class_name VOwnerGate
## Exact port of www/proto3d/ownergate.js (local mode). Same salt/hash/iterations; PBKDF2-HMAC-SHA256, 32-byte key.
## Only the salt + hash are here; the passphrase is never stored, logged or printed.
## Server mode (Firebase claims) is kept as set_server_owner_provider(callable) like the JS.
const GATE := {"v": 2, "salt": "150a1c54ab232044870dcb521f1468ba", "hash": "6a14971cd36e613ecebccedf46344f1fcf74bef61c0be542baad29048733c480", "iter": 210000}
const OWNER_UID_ALLOWLIST := []
const UNLOCK_KEY := "vn_owner_unlock_v2"
const THROTTLE_KEY := "vn_owner_attempts_v2"
const FREE_TRIES := 3
const LOCK_BASE_MS := 30000
const LOCK_MAX_MS := 3600000
const MAX_PASS_LEN := 128

var params: Dictionary = GATE
var dir := "user://"
var now_ms: Callable = func() -> int: return int(Time.get_unix_time_from_system() * 1000)
var provider = null

static func pbkdf2_sha256(pw: PackedByteArray, salt: PackedByteArray, iter: int, dk_len := 32) -> PackedByteArray:
	var out := PackedByteArray()
	var block := 1
	while out.size() < dk_len:
		var s := salt.duplicate()
		s.append_array(PackedByteArray([(block >> 24) & 255, (block >> 16) & 255, (block >> 8) & 255, block & 255]))
		var u := _hmac(pw, s)
		var acc := u.to_int64_array()
		for _i in range(1, iter):
			u = _hmac(pw, u)
			var ui := u.to_int64_array()
			acc[0] ^= ui[0]; acc[1] ^= ui[1]; acc[2] ^= ui[2]; acc[3] ^= ui[3]
		out.append_array(acc.to_byte_array())
		block += 1
	return out.slice(0, dk_len)

static func _hmac(key: PackedByteArray, msg: PackedByteArray) -> PackedByteArray:
	var h := HMACContext.new()
	h.start(HashingContext.HASH_SHA256, key); h.update(msg)
	return h.finish()

static func derive(pw: String, salt_hex: String, iter: int) -> String:
	return pbkdf2_sha256(pw.to_utf8_buffer(), salt_hex.hex_decode(), iter).hex_encode()

static func sha256_hex(t: String) -> String: return t.sha256_text()
static func unlock_token(p: Dictionary) -> String: return sha256_hex(str(p.hash) + ":unlock:v" + str(p.v))

static func const_eq(a: String, b: String) -> bool:
	if a.length() != b.length(): return false
	var r := 0
	for i in a.length(): r |= a.unicode_at(i) ^ b.unicode_at(i)
	return r == 0

static func owner_from_claims(claims, allowlist = OWNER_UID_ALLOWLIST) -> bool:
	if claims is bool: return claims
	if typeof(claims) != TYPE_DICTIONARY: return false
	var uid = claims.get("uid", claims.get("user_id", claims.get("sub")))
	return claims.get("owner") == true or (uid is String and allowlist.has(uid))

func _sget(k: String):
	var p := dir + k
	if not FileAccess.file_exists(p): return null
	return FileAccess.get_file_as_string(p)
func _sput(k: String, v: String) -> void:
	var f := FileAccess.open(dir + k, FileAccess.WRITE)
	if f: f.store_string(v)
func _sdel(k: String) -> void:
	if FileAccess.file_exists(dir + k): DirAccess.remove_absolute(dir + k)

func mode() -> String: return "server" if provider else "local"
func set_server_owner_provider(fn) -> void: provider = fn if fn is Callable else null

func read_attempts() -> Dictionary:
	var raw = _sget(THROTTLE_KEY)
	if raw is String:
		var a = JSON.parse_string(raw)
		if typeof(a) == TYPE_DICTIONARY and a.has("fails") and a.has("until"): return {"fails": maxi(0, int(a.fails)), "until": int(a.until)}
	return {"fails": 0, "until": 0}

func retry_ms() -> int: return maxi(0, read_attempts().until - now_ms.call())
func status() -> Dictionary:
	var a := read_attempts(); var t: int = now_ms.call()
	return {"mode": mode(), "fails": a.fails, "locked": a.until > t, "retryMs": maxi(0, a.until - t)}

func is_owner() -> bool:
	if provider: return owner_from_claims(provider.call())
	var t = _sget(UNLOCK_KEY)
	return t is String and t != "" and const_eq(t, unlock_token(params))

## Returns {ok, reason?, retryMs?, triesLeft?}. Slow (210k iterations): call from a Thread (see unlock_async).
func unlock(pw) -> Dictionary:
	if provider: return {"ok": false, "reason": "server-mode"}
	var a := read_attempts(); var t: int = now_ms.call()
	if a.until > t: return {"ok": false, "reason": "throttled", "retryMs": a.until - t}
	if not (pw is String) or pw.length() == 0 or pw.length() > MAX_PASS_LEN: return fail(a, t)
	var got := derive(pw.strip_edges(), params.salt, int(params.iter))
	if const_eq(got, params.hash):
		_sdel(THROTTLE_KEY); _sput(UNLOCK_KEY, unlock_token(params))
		return {"ok": true}
	return fail(a, t)

func fail(a: Dictionary, t: int) -> Dictionary:
	var fails: int = a.fails + 1
	var over := fails - FREE_TRIES
	var wait: int = mini(LOCK_MAX_MS, LOCK_BASE_MS * int(pow(2, over))) if over >= 0 else 0
	_sput(THROTTLE_KEY, JSON.stringify({"fails": fails, "until": t + wait if wait else 0}))
	return {"ok": false, "reason": "throttled" if wait else "wrong", "retryMs": wait, "triesLeft": maxi(0, FREE_TRIES - fails)}

func lock() -> void: _sdel(UNLOCK_KEY)

## Runs unlock() on a worker thread and calls done(result) on the main thread.
func unlock_async(pw: String, done: Callable) -> void:
	var th := Thread.new()
	th.start(func():
		var r := unlock(pw)
		(func(): th.wait_to_finish(); done.call(r)).call_deferred())
