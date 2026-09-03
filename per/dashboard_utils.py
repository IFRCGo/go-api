from unicodedata import category, normalize

AREA_NAMES = {
    1: "Policy Strategy and Standards",
    2: "Analysis and planning",
    3: "Operational capacity",
    4: "Coordination",
    5: "Operations support",
}

AFFIRMATIVE_WORDS = {
    "yes",
    "si",
    "sí",
    "oui",
    "da",
    "ja",
    "sim",
    "aye",
    "yep",
    "igen",
    "hai",
    "evet",
    "是",
    "はい",
    "예",
    "نعم",
}


def contains_affirmative(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False

    normalized = normalize("NFD", value.casefold())
    normalized = "".join(character for character in normalized if category(character) != "Mn")
    return any(word in normalized for word in AFFIRMATIVE_WORDS)
