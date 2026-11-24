"""ISO 286-2 tolerance calculator.

Looks up limit deviations from the ISO 286-2:2010 tables (nominal sizes
3-400 mm) and computes limits, GO / NO-GO ends and measurement verdicts.

Data source: the ISO 286-2:2010 limit-deviation tables, values in
micrometres as [upper, lower] pairs. The F6/F7/F8 hole rows follow the
fundamental-deviation + IT computation noted in the source sheet.
Only the classes present in the tables are covered; anything else raises
ValueError instead of guessing a deviation.

Verdict rules (same as a gauge inspection sheet):
- Not OK: a measured value lies outside [lower limit, upper limit].
- Hati-Hati: inside, but within 10% of the tolerance width from a limit.
- OK: inside and not near a limit.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

__all__ = [
    "deviations",
    "limits",
    "tolerance_width",
    "go_nogo",
    "verdict",
    "verdict_one",
    "covered_classes",
    "size_range",
]

_TABLES = json.loads((Path(__file__).with_name("tables.json")).read_text(encoding="utf-8"))
_STEPS = [(Decimal(str(lo)), Decimal(str(hi))) for lo, hi in _TABLES["steps_mm"]]
_SHAFT = _TABLES["shaft"]
_HOLE = _TABLES["hole"]

MIN_NOMINAL = _STEPS[0][0]  # 3 mm, exclusive: first step is (3, 6]
MAX_NOMINAL = _STEPS[-1][1]  # 400 mm, inclusive

_OK = "OK"
_HATI_HATI = "Hati-Hati"
_NOT_OK = "Not OK"


def size_range() -> tuple[float, float]:
    """Covered nominal-size range in mm: (3, 400]."""
    return (float(MIN_NOMINAL), float(MAX_NOMINAL))


def covered_classes() -> dict[str, list[str]]:
    """Tolerance classes covered by the tables, per kind."""
    return {"shaft": sorted(_SHAFT), "hole": sorted(_HOLE)}


def _kind_and_class(cls: str) -> tuple[str, str]:
    """Split a tolerance class into ('shaft'|'hole', class) or raise."""
    if not isinstance(cls, str) or not cls:
        raise ValueError("tolerance class must be a non-empty string, e.g. 'H7' or 'h7'")
    cls = cls.strip()
    letters = "".join(ch for ch in cls if ch.isalpha())
    if not letters or not cls[len(letters):].isdigit():
        raise ValueError(
            f"bad tolerance class {cls!r}: expected a letter code plus a grade number, e.g. 'H7'"
        )
    if letters.isupper():
        table, kind = _HOLE, "hole"
    elif letters.islower():
        table, kind = _SHAFT, "shaft"
    else:
        raise ValueError(
            f"bad tolerance class {cls!r}: use all capitals for a hole (e.g. 'H7') "
            f"or all lowercase for a shaft (e.g. 'h7')"
        )
    if cls not in table:
        covered = ", ".join(sorted(table))
        raise ValueError(
            f"tolerance class {cls!r} is not in the ISO 286-2 tables shipped here. "
            f"Covered {kind} classes: {covered}."
        )
    return kind, cls


def _step_index(nominal: Decimal) -> int:
    if nominal <= MIN_NOMINAL or nominal > MAX_NOMINAL:
        raise ValueError(
            f"nominal size {nominal} mm is outside the covered range "
            f"(over {MIN_NOMINAL} up to {MAX_NOMINAL} mm)"
        )
    for i, (lo, hi) in enumerate(_STEPS):
        if lo < nominal <= hi:
            return i
    raise ValueError(f"no size step covers nominal {nominal} mm")  # pragma: no cover


def deviations(nominal: float | str | Decimal, cls: str) -> tuple[Decimal, Decimal]:
    """Limit deviations in micrometres as (upper, lower) for nominal + class."""
    nominal = Decimal(str(nominal))
    kind, cls = _kind_and_class(cls)
    table = _HOLE if kind == "hole" else _SHAFT
    upper_um, lower_um = table[cls][_step_index(nominal)]
    return Decimal(str(upper_um)), Decimal(str(lower_um))


def limits(nominal: float | str | Decimal, cls: str) -> tuple[float, float]:
    """Lower and upper limits in mm as (lower, upper)."""
    nominal = Decimal(str(nominal))
    upper_um, lower_um = deviations(nominal, cls)
    lower = nominal + lower_um / Decimal(1000)
    upper = nominal + upper_um / Decimal(1000)
    return float(lower), float(upper)


def tolerance_width(nominal: float | str | Decimal, cls: str) -> float:
    """Tolerance width (upper limit minus lower limit) in mm."""
    lower, upper = limits(nominal, cls)
    return upper - lower


def go_nogo(nominal: float | str | Decimal, cls: str) -> tuple[float, float]:
    """GO and NO-GO ends in mm as (GO, NO-GO).

    Hole (capital letter): GO is the smaller limit, NO-GO the larger one.
    Shaft (lowercase letter): GO is the larger limit, NO-GO the smaller one.
    """
    kind, _ = _kind_and_class(cls)
    lower, upper = limits(nominal, cls)
    return (lower, upper) if kind == "hole" else (upper, lower)


def verdict_one(value: float | str | Decimal, lower: float, upper: float) -> str:
    """Verdict for one measured value against limits in mm."""
    value = Decimal(str(value))
    lower, upper = Decimal(str(lower)), Decimal(str(upper))
    if value < lower or value > upper:
        return _NOT_OK
    width = upper - lower
    if width > 0 and (value - lower <= width / 10 or upper - value <= width / 10):
        return _HATI_HATI
    return _OK


def verdict(
    nominal: float | str | Decimal,
    cls: str,
    go: float | str | Decimal | None = None,
    nogo: float | str | Decimal | None = None,
) -> dict:
    """Verdict for measured GO and/or NO-GO values.

    Returns {"go": verdict | None, "nogo": verdict | None, "overall": verdict}.
    The overall verdict is the worst of the filled ends:
    Not OK beats Hati-Hati beats OK.
    """
    lower, upper = limits(nominal, cls)
    result: dict = {"go": None, "nogo": None, "overall": _OK}
    for key, actual in (("go", go), ("nogo", nogo)):
        if actual is not None:
            result[key] = verdict_one(actual, lower, upper)
    filled = [v for v in (result["go"], result["nogo"]) if v is not None]
    if _NOT_OK in filled:
        result["overall"] = _NOT_OK
    elif _HATI_HATI in filled:
        result["overall"] = _HATI_HATI
    return result
