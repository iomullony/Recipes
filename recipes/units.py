from decimal import Decimal

# Physical (density-independent) conversions, grouped by family and expressed
# relative to one base unit per family. Only units within the same family can
# be safely compared/converted - e.g. grams and cups are not interchangeable
# without knowing the ingredient's density, so they're treated as unrelated.

MASS_TO_GRAMS = {
    "g": Decimal("1"),
    "kg": Decimal("1000"),
    "oz": Decimal("28.3495"),
    "lb": Decimal("453.592"),
}

VOLUME_TO_ML = {
    "mL": Decimal("1"),
    "L": Decimal("1000"),
    "cups": Decimal("236.588"),
    "tbsp": Decimal("14.7868"),
    "tsp": Decimal("4.92892"),
}


def unit_family_and_factor(unit):
    """Return (family_key, factor_to_base_unit) for a unit string.

    Units in the same family can be summed/compared after multiplying by their
    factor. Unknown or count-like units (e.g. "unit(s)", "", or anything not
    in the tables above) get their own family keyed by the literal unit text,
    so they only ever match an identical unit string.
    """
    normalized = (unit or "").strip()
    if normalized in MASS_TO_GRAMS:
        return "mass", MASS_TO_GRAMS[normalized]
    if normalized in VOLUME_TO_ML:
        return "volume", VOLUME_TO_ML[normalized]
    return f"unit:{normalized.lower()}", Decimal("1")
