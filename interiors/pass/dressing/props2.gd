class_name InteriorProps2
## Pass 2 procedural props (batched into InteriorDressing.Batch; visual only, no colliders). Kit props face +Z.

## purpose themes: weighted clutter per building (ids from InteriorDefs / InteriorExtraDefs, variant suffix stripped)
const THEME := {
	"inn": ["barrels", "crates", "shelf_bottles", "firewood", "sacks", "barrels"], "guildhall": ["shelf_books", "crates", "weapons", "candles", "chest_pile"],
	"smithy": ["coal", "quench", "weapons", "ingots", "firewood", "bucket"], "bakery": ["flour", "flour", "barrels", "shelf_jars", "firewood"],
	"apothecary": ["shelf_jars", "shelf_bottles", "herbs", "crates", "candles"], "townhall": ["shelf_books", "scrolls", "candles", "crates"],
	"temple": ["candles", "candles", "urns", "shelf_books"], "library": ["shelf_books", "shelf_books", "scrolls", "candles", "globe"],
	"mage": ["shelf_jars", "shelf_books", "candles", "globe", "crates"], "treasury": ["chest_pile", "ingots", "crates", "barrels"],
	"keep": ["weapons", "barrels", "chest_pile", "candles", "shelf_books", "urns"], "observatory": ["globe", "armillary", "shelf_books", "scrolls", "candles"],
	"crypt": ["candles", "urns", "urns", "crates"], "market": ["crates", "sacks", "barrels", "baskets", "crates"],
	"training": ["weapons", "dummy", "barrels", "crates", "dummy"], "colosseum": ["weapons", "barrels", "crates", "dummy"],
	"thieves": ["crates", "barrels", "sacks", "candles", "chest_pile"], "farmhouse": ["sacks", "firewood", "barrels", "baskets", "shelf_jars"],
	"barn": ["hay", "hay", "sacks", "barrels", "crates"], "stables": ["hay", "hay", "bucket", "sacks"], "windmill": ["flour", "flour", "sacks", "crates"],
	"house1": ["shelf_jars", "firewood", "baskets", "bucket"], "house2": ["barrels", "firewood", "shelf_bottles", "sacks"],
	"house3": ["baskets", "crates", "shelf_jars", "herbs"], "house4": ["firewood", "bucket", "shelf_books", "barrels"],
	"harbour_warehouse": ["crates", "crates", "barrels", "rope", "sacks", "crates"], "harbour_shop": ["shelf_bottles", "rope", "crates", "barrels", "baskets"],
	"harbour_house": ["rope", "firewood", "bucket", "baskets"], "gatetower": ["weapons", "barrels", "crates", "firewood"],
	"lighthouse": ["barrels", "rope", "crates"]}
## what sits on tables / counters
const TOP := {"inn": "mugs", "guildhall": "maps", "keep": "maps", "townhall": "scrolls", "library": "books", "mage": "potions", "apothecary": "potions",
	"observatory": "maps", "bakery": "bread", "market": "bread", "smithy": "tools", "training": "mugs", "thieves": "coins", "treasury": "coins"}

static func X(p: Vector3, rot: float) -> Transform3D: return Transform3D(Basis(Vector3.UP, rot), p)

static func build(B, kind: String, xf: Transform3D, rng: RandomNumberGenerator, hi: bool) -> void:
	var seg := 10 if hi else 6
	match kind:
		"crates":
			var n := rng.randi_range(1, 3) if hi else 1
			for k in n:
				var s := rng.randf_range(0.5, 0.75); var o := Vector3(rng.randf_range(-0.35, 0.35) * float(k > 0), 0, rng.randf_range(-0.1, 0.1))
				var y := 0.0 if k < 2 else 0.6
				crate(B, xf * X(o + Vector3(0, y, 0), rng.randf_range(-0.3, 0.3)), s, hi)
		"chest_pile":
			crate(B, xf * X(Vector3(-0.3, 0, 0), 0.1), 0.6, hi); if hi: crate(B, xf * X(Vector3(0.35, 0, 0.05), -0.2), 0.5, hi); crate(B, xf * X(Vector3(0, 0.6, 0), 0.4), 0.45, hi)
		"barrels", "quench":
			var n := (rng.randi_range(1, 3) if kind == "barrels" else 1) if hi else 1
			for k in n: barrel(B, xf * X(Vector3((k - (n - 1) / 2.0) * 0.62, 0, rng.randf_range(-0.08, 0.08)), rng.randf() * TAU), seg, hi, kind == "quench")
			if hi and n == 3: barrel(B, xf * X(Vector3(0, 0.88, 0), 0.0), seg, hi, false)
		"sacks", "flour":
			var n := rng.randi_range(2, 4) if hi else 1
			for k in n: sack(B, xf * X(Vector3((k % 3 - 1) * 0.45, 0.0 if k < 3 else 0.42, rng.randf_range(-0.12, 0.12)), rng.randf() * TAU), seg, "paper" if kind == "flour" else "cloth")
		"hay":
			for k in (2 if hi else 1): B.box(xf * X(Vector3(0, 0.3 + k * 0.6, 0), rng.randf_range(-0.2, 0.2)), Vector3(1.1, 0.58, 0.55), "hay")
		"firewood", "coal":
			if kind == "coal":
				B.cyl(xf * X(Vector3(0, 0.15, 0), 0), 0.55, 0.3, seg, "coal", 0.25); B.box(xf * X(Vector3(0.5, 0.05, 0.4), 0.3), Vector3(0.25, 0.1, 0.4), "iron")
			else:
				for r in (4 if hi else 2):
					for k in (6 - r if hi else 3 - r):
						var p := Vector3((k - (5 - r) / 2.0) * 0.16, 0.08 + r * 0.14, 0)
						B.cyl(xf * Transform3D(Basis(Vector3.RIGHT, PI / 2), p), 0.07, 0.9, 6 if hi else 5, "darkoak")
		"bucket":
			B.cyl(xf * X(Vector3(0, 0.2, 0), 0), 0.17, 0.4, seg, "darkoak", 0.21)
			if hi: B.cyl(xf * X(Vector3(0, 0.33, 0), 0), 0.215, 0.04, seg, "iron"); B.cyl(xf * X(Vector3(0, 0.12, 0), 0), 0.19, 0.04, seg, "iron")
		"rope":
			for k in (3 if hi else 1): B.cyl(xf * X(Vector3(0, 0.06 + k * 0.1, 0), 0), 0.38 - k * 0.05, 0.1, seg, "cloth")
		"shelf_bottles", "shelf_jars", "shelf_books", "herbs", "scrolls":
			shelf(B, xf, kind, rng, hi)
		"candles":
			B.cyl(xf * X(Vector3(0, 0.45, 0), 0), 0.04, 0.9, 6, "iron"); B.cyl(xf * X(Vector3(0, 0.02, 0), 0), 0.22, 0.04, seg, "iron")
			B.cyl(xf * X(Vector3(0, 0.92, 0), 0), 0.25, 0.04, seg, "iron")
			for k in (5 if hi else 3):
				var a := TAU * k / (5 if hi else 3); var hgt := rng.randf_range(0.12, 0.3); var p := Vector3(cos(a) * 0.18, 0.94 + hgt / 2, sin(a) * 0.18)
				B.cyl(xf * X(p, 0), 0.025, hgt, 6, "paper"); B.box(xf * X(p + Vector3(0, hgt / 2 + 0.03, 0), 0), Vector3(0.025, 0.05, 0.025), "flame")
		"urns":
			for k in (2 if hi else 1): B.cyl(xf * X(Vector3(k * 0.5 - 0.25 * float(hi), 0.35, 0), 0), 0.13, 0.7, seg, "clay", 0.1, 0.12 if hi else 0.0)
		"ingots":
			crate(B, xf, 0.6, hi)
			for k in (6 if hi else 2): B.box(xf * X(Vector3((k % 3 - 1) * 0.16, 0.63 + (k / 3) * 0.05, (k / 3) * 0.02 - 0.08), 0), Vector3(0.14, 0.05, 0.3), "gold" if k % 2 == 0 else "iron")
		"weapons":
			B.box(xf * X(Vector3(0, 0.12, 0), 0), Vector3(1.4, 0.1, 0.3), "darkoak"); B.box(xf * X(Vector3(0, 1.45, -0.05), 0), Vector3(1.4, 0.08, 0.1), "darkoak")
			for sx in [-0.68, 0.68]: B.box(xf * X(Vector3(sx, 0.8, -0.05), 0), Vector3(0.08, 1.6, 0.08), "darkoak")
			for k in (5 if hi else 3):
				var x := -0.5 + k * (1.0 / ((5 if hi else 3) - 1)); var tilt := Basis(Vector3.FORWARD, rng.randf_range(-0.05, 0.05))
				B.cyl(xf * Transform3D(tilt, Vector3(x, 1.0, 0)), 0.02, 1.8, 5, "darkoak")
				B.box(xf * X(Vector3(x, 1.95, 0), 0), Vector3(0.05, 0.22, 0.015), "iron")
			if hi:
				B.cyl(xf * Transform3D(Basis(Vector3.RIGHT, PI / 2), Vector3(0.0, 0.55, 0.14)), 0.32, 0.05, 12, "redcloth")
				B.cyl(xf * Transform3D(Basis(Vector3.RIGHT, PI / 2), Vector3(0.0, 0.55, 0.17)), 0.08, 0.04, 8, "iron")
		"dummy":
			B.cyl(xf * X(Vector3(0, 0.8, 0), 0), 0.05, 1.6, 6, "darkoak"); B.box(xf * X(Vector3(0, 1.35, 0), 0), Vector3(0.9, 0.08, 0.08), "darkoak")
			sack(B, xf * X(Vector3(0, 0.95, 0), 0), seg, "cloth", 0.28, 0.7); B.cyl(xf * X(Vector3(0, 1.62, 0), 0), 0.14, 0.28, seg, "cloth", 0.14, 0.04)
		"baskets":
			for k in (2 if hi else 1):
				var p := Vector3(k * 0.5 - 0.25, 0.14, 0)
				B.cyl(xf * X(p, 0), 0.2, 0.28, seg, "hay", 0.25)
				if hi: for j in 4: B.cyl(xf * X(p + Vector3((j % 2 - 0.5) * 0.14, 0.17, (j / 2 - 0.5) * 0.14), 0), 0.07, 0.12, 6, ["glassr", "clay", "hay", "glassb"][j], 0.05, 0.03)
		"globe":
			B.cyl(xf * X(Vector3(0, 0.4, 0), 0), 0.05, 0.8, 6, "brass"); B.cyl(xf * X(Vector3(0, 0.03, 0), 0), 0.3, 0.06, seg, "darkoak")
			B.cyl(xf * X(Vector3(0, 1.08, 0), 0), 0.02, 0.56, seg, "glassb", 0.02, 0.28)
			if hi: ring(B, xf * Transform3D(Basis(Vector3.FORWARD, 0.4), Vector3(0, 1.08, 0)), 0.33, 16, "brass")
		"armillary":
			B.cyl(xf * X(Vector3(0, 0.5, 0), 0), 0.06, 1.0, 8, "brass"); B.cyl(xf * X(Vector3(0, 0.04, 0), 0), 0.35, 0.08, seg, "iron")
			for k in (3 if hi else 1): ring(B, xf * Transform3D(Basis(Vector3.UP, k * 1.05) * Basis(Vector3.FORWARD, 0.4 + k * 0.6), Vector3(0, 1.4, 0)), 0.45 - k * 0.04, 20 if hi else 10, "brass")
			B.cyl(xf * X(Vector3(0, 1.4, 0), 0), 0.02, 0.16, 8, "gold", 0.02, 0.08)

static func ring(B, xf: Transform3D, r: float, n: int, kind: String) -> void:
	for k in n:
		var a := TAU * (k + 0.5) / n
		B.box(xf * Transform3D(Basis(Vector3.FORWARD, -a), Vector3(cos(a) * r, sin(a) * r, 0)), Vector3(0.03, TAU * r / n + 0.01, 0.03), kind)

static func crate(B, xf: Transform3D, s: float, hi: bool) -> void:
	B.box(xf * X(Vector3(0, s / 2, 0), 0), Vector3(s, s, s) * 0.94, "oak")
	if not hi: return
	for e in [[Vector3(0, 0.03, 0), Vector3(s, 0.06, s)], [Vector3(0, s - 0.03, 0), Vector3(s, 0.06, s)]]:
		B.box(xf * X(e[0], 0), e[1], "darkoak")
	for c in [Vector3(-1, 0, -1), Vector3(1, 0, -1), Vector3(-1, 0, 1), Vector3(1, 0, 1)]:
		B.box(xf * X(Vector3(c.x * s / 2 * 0.97, s / 2, c.z * s / 2 * 0.97), 0), Vector3(0.07, s, 0.07), "darkoak")
	B.box(xf * Transform3D(Basis(Vector3.BACK, 0.785), Vector3(0, s / 2, s / 2 * 0.95)), Vector3(0.06, s * 1.3, 0.03), "darkoak")   # diagonal brace

static func barrel(B, xf: Transform3D, seg: int, hi: bool, water: bool) -> void:
	B.cyl(xf * X(Vector3(0, 0.42, 0), 0), 0.25, 0.84, seg + 2 if hi else seg, "oak", 0.25, 0.06 if hi else 0.0)
	if hi:
		for y in [0.1, 0.32, 0.52, 0.74]: B.cyl(xf * X(Vector3(0, y, 0), 0), 0.265 + 0.04 * sin(PI * y / 0.84), 0.035, seg + 2, "iron")
	if water: B.cyl(xf * X(Vector3(0, 0.8, 0), 0), 0.24, 0.02, seg, "glassb")

static func sack(B, xf: Transform3D, seg: int, kind: String, r := 0.24, h := 0.55) -> void:
	B.cyl(xf * X(Vector3(0, h / 2, 0), 0), r * 0.9, h, seg, kind, r * 0.45, r * 0.35)

static func shelf(B, xf: Transform3D, kind: String, rng: RandomNumberGenerator, hi: bool) -> void:
	var w := 1.2; var dd := 0.38; var hh := 1.9
	for sx in [-1, 1]: B.box(xf * X(Vector3(sx * w / 2, hh / 2, 0), 0), Vector3(0.05, hh, dd), "darkoak")
	B.box(xf * X(Vector3(0, hh / 2, -dd / 2 + 0.01), 0), Vector3(w, hh, 0.02), "darkoak")
	var levels := [0.08, 0.55, 1.0, 1.45, 1.88]
	for y in levels: B.box(xf * X(Vector3(0, y, 0), 0), Vector3(w, 0.04, dd), "oak")
	if not hi and rng.randf() < 0.5: return
	for li in levels.size() - 1:
		var y: float = levels[li] + 0.02; var x := -w / 2 + 0.1
		while x < w / 2 - 0.1:
			match kind:
				"shelf_books", "scrolls":
					if kind == "scrolls" and li % 2 == 1:
						B.cyl(xf * Transform3D(Basis(Vector3.FORWARD, PI / 2), Vector3(x + 0.1, y + 0.06, 0.02)), 0.05, 0.3, 6, "paper"); x += 0.14; continue
					var bw := rng.randf_range(0.04, 0.09); var bh := rng.randf_range(0.24, 0.38)
					B.box(xf * X(Vector3(x + bw / 2, y + bh / 2, 0.02), 0), Vector3(bw, bh, 0.26), ["redcloth", "darkoak", "cloth", "glassb", "clay"][rng.randi() % 5])
					x += bw + 0.005
				"shelf_bottles":
					var hb := rng.randf_range(0.2, 0.32); B.cyl(xf * X(Vector3(x + 0.05, y + hb / 2, 0.02), 0), 0.045, hb, 6 if hi else 5, ["glassb", "glassr", "clay"][rng.randi() % 3], 0.02, 0.01)
					x += 0.12
				"shelf_jars", "herbs":
					var hj := rng.randf_range(0.14, 0.24); B.cyl(xf * X(Vector3(x + 0.07, y + hj / 2, 0.02), 0), 0.065, hj, 6 if hi else 5, ["clay", "glassb", "paper"][rng.randi() % 3], 0.05, 0.02)
					if kind == "herbs" and li == 3: B.box(xf * X(Vector3(x + 0.07, y + 0.55, 0.12), 0), Vector3(0.08, 0.3, 0.05), "hay")
					x += 0.16
		if not hi: break

## clutter on a table / counter top (y = top height)
static func top(B, xf: Transform3D, kind: String, rng: RandomNumberGenerator, hi: bool, w: float, d: float) -> void:
	var n := (rng.randi_range(3, 6) if hi else 2)
	for k in n:
		var p := Vector3(rng.randf_range(-w / 2 + 0.15, w / 2 - 0.15), 0, rng.randf_range(-d / 2 + 0.12, d / 2 - 0.12))
		match kind:
			"mugs": B.cyl(xf * X(p + Vector3(0, 0.06, 0), 0), 0.045, 0.12, 6, "darkoak" if k % 2 else "clay")
			"maps", "scrolls": B.box(xf * X(p + Vector3(0, 0.005, 0), rng.randf() * TAU), Vector3(0.42, 0.01, 0.3), "paper")
			"books": B.box(xf * X(p + Vector3(0, 0.03, 0), rng.randf() * TAU), Vector3(0.22, 0.06, 0.3), "redcloth")
			"potions": B.cyl(xf * X(p + Vector3(0, 0.09, 0), 0), 0.04, 0.18, 6, "glassb" if k % 2 else "glassr", 0.015, 0.02)
			"bread": B.cyl(xf * Transform3D(Basis(Vector3.RIGHT, PI / 2), p + Vector3(0, 0.05, 0)), 0.06, 0.24, 6, "clay", 0.06, 0.02)
			"tools": B.box(xf * X(p + Vector3(0, 0.02, 0), rng.randf() * TAU), Vector3(0.05, 0.04, 0.35), "iron")
			"coins": B.cyl(xf * X(p + Vector3(0, 0.02, 0), 0), 0.08, 0.04, 8, "gold")
	if hi and kind in ["maps", "scrolls", "books", "potions"]:   # candle
		var p := Vector3(w / 2 - 0.2, 0, -d / 2 + 0.18)
		B.cyl(xf * X(p + Vector3(0, 0.1, 0), 0), 0.03, 0.2, 6, "paper"); B.box(xf * X(p + Vector3(0, 0.23, 0), 0), Vector3(0.025, 0.05, 0.025), "flame")
