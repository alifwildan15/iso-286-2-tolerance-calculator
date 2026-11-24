"""Command-line interface for the ISO 286-2 tolerance calculator.

Usage:
    python -m iso286 22 H7
    python -m iso286 220 F8 --go 220.051 --nogo 220.13
    python -m iso286 22 H7 --measure 22.011
    python -m iso286 --list-classes
    python -m iso286 --list-classes hole
    python -m iso286 22 H7 --json
"""

from __future__ import annotations

import argparse
import json
import sys

from .calculator import (
    covered_classes,
    deviations,
    go_nogo,
    limits,
    size_range,
    tolerance_width,
    verdict,
)


def _fmt_dev(value) -> str:
    """Format a deviation in µm: +21, 0, -21 (no '+0')."""
    return "0" if value == 0 else f"{value:+g}"


def _fmt(value: float) -> str:
    """Format an mm value with up to 4 decimals, no trailing zeros."""
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text not in ("-0", "") else "0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iso286",
        description="ISO 286-2 tolerance calculator (nominal 3-400 mm).",
    )
    parser.add_argument("nominal", nargs="?", help="nominal size in mm, e.g. 22")
    parser.add_argument("tolerance_class", nargs="?", help="tolerance class, e.g. H7 or h7")
    parser.add_argument("--go", default=None, help="measured GO value in mm")
    parser.add_argument("--nogo", default=None, help="measured NO-GO value in mm")
    parser.add_argument("--measure", default=None, help="single measured value in mm")
    parser.add_argument(
        "--list-classes",
        nargs="?",
        const="all",
        choices=("all", "shaft", "hole"),
        help="list the covered tolerance classes and exit",
    )
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)

    if args.list_classes is not None:
        classes = covered_classes()
        if args.list_classes == "all":
            print("shaft: " + ", ".join(classes["shaft"]))
            print("hole:  " + ", ".join(classes["hole"]))
        else:
            print(", ".join(classes[args.list_classes]))
        return 0

    if args.nominal is None or args.tolerance_class is None:
        parser.error("nominal size and tolerance class are required")

    try:
        upper_um, lower_um = deviations(args.nominal, args.tolerance_class)
        lower, upper = limits(args.nominal, args.tolerance_class)
        go, nogo = go_nogo(args.nominal, args.tolerance_class)
        width = tolerance_width(args.nominal, args.tolerance_class)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    measured = {}
    if args.measure is not None:
        measured["measure"] = args.measure
    if args.go is not None:
        measured["go"] = args.go
    if args.nogo is not None:
        measured["nogo"] = args.nogo
    verdicts = None
    if measured:
        verdicts = verdict(
            args.nominal,
            args.tolerance_class,
            go=measured.get("go", measured.get("measure")),
            nogo=measured.get("nogo"),
        )
        if "measure" in measured and "go" not in measured and "nogo" not in measured:
            verdicts = {"measure": verdicts["go"], "overall": verdicts["overall"]}

    if args.json:
        out = {
            "nominal_mm": float(args.nominal),
            "tolerance_class": args.tolerance_class,
            "deviation_um": {"upper": float(upper_um), "lower": float(lower_um)},
            "limits_mm": {"lower": lower, "upper": upper},
            "tolerance_width_mm": width,
            "go_mm": go,
            "nogo_mm": nogo,
        }
        if verdicts is not None:
            out["verdict"] = verdicts
        print(json.dumps(out, indent=2))
        return 0

    lo, hi = size_range()
    print(f"{args.nominal} {args.tolerance_class}  (ISO 286-2, nominal over {lo:g} up to {hi:g} mm)")
    print(f"deviations: {_fmt_dev(upper_um)} / {_fmt_dev(lower_um)} µm (upper / lower)")
    print(f"limits:     {_fmt(lower)} - {_fmt(upper)} mm")
    print(f"width:      {_fmt(width)} mm")
    print(f"GO:         {_fmt(go)} mm")
    print(f"NO-GO:      {_fmt(nogo)} mm")
    if verdicts is not None:
        for key in ("measure", "go", "nogo"):
            if key in verdicts and verdicts[key] is not None:
                print(f"verdict {key}: {verdicts[key]}")
        print(f"overall:    {verdicts['overall']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
