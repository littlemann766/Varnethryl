class_name Wallet
## Beth stage 10: STUB of the coin + inventory API the Saltglass lift calls (spec: README_LUCKY.md, Stage 10).
## Lucky owns the real wallet/inventory/save. Keep these signatures and back them with your systems; this stub only exists
## so the lift scene runs on its own. Save keys used by the stub (and suggested for the real save): "wallet.coins" (int),
## "inventory.items" (Dictionary item_id -> count).
const PATH := "user://wallet_stub.cfg"
const ITEMS := {
	"saltglass_lift_pass": {"name": "Saltglass Lift Season Pass", "price": 150, "stack": 1, "kind": "key_item"},
}
static func _cfg() -> ConfigFile:
	var c := ConfigFile.new(); c.load(PATH); return c
static func coins() -> int: return int(_cfg().get_value("wallet", "coins", 0))
static func add_coins(n: int, reason := "") -> void:
	var c := _cfg(); c.set_value("wallet", "coins", maxi(0, int(c.get_value("wallet", "coins", 0)) + n)); c.save(PATH)
## Takes `amount` coins if the player has them. Returns false (and takes nothing) if not.
static func pay(amount: int, reason := "") -> bool:
	if amount <= 0: return true
	if coins() < amount: return false
	add_coins(-amount, reason); return true
static func has_item(id: String) -> bool: return item_count(id) > 0
static func item_count(id: String) -> int: return int((_cfg().get_value("inventory", "items", {}) as Dictionary).get(id, 0))
static func give_item(id: String, n := 1) -> void:
	var c := _cfg(); var it: Dictionary = c.get_value("inventory", "items", {}); var st := int(ITEMS.get(id, {}).get("stack", 99))
	it[id] = mini(st, int(it.get(id, 0)) + n); c.set_value("inventory", "items", it); c.save(PATH)
## pay + give in one go (shops). Returns false if the player can't afford it or already holds a stack-1 item.
static func buy(id: String) -> bool:
	var d: Dictionary = ITEMS[id]
	if int(d.stack) == 1 and has_item(id): return false
	if not pay(int(d.price), "buy:" + id): return false
	give_item(id); return true
