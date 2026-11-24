"""ISO 286-2 tolerance calculator: limits, GO / NO-GO and verdicts."""

from .calculator import (
    covered_classes,
    deviations,
    go_nogo,
    limits,
    size_range,
    tolerance_width,
    verdict,
    verdict_one,
)

__version__ = "1.0.0"

__all__ = [
    "covered_classes",
    "deviations",
    "go_nogo",
    "limits",
    "size_range",
    "tolerance_width",
    "verdict",
    "verdict_one",
    "__version__",
]
