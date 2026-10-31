class_name RegexHelper
static var _re: RegEx
## companions.js rangedRe
static func ranged(id: String) -> bool:
	if _re == null: _re = RegEx.create_from_string("(?i)seraphine|zephyr|lunara|marella|ember|pip|wren|elira|mage|phoenix")
	return _re.search(id) != null
