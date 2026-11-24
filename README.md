# ISO 286-2 Tolerance Calculator

A small Python tool that looks up limit deviations from the **ISO 286-2:2010**
tables and computes limits, GO / NO-GO ends and measurement verdicts for a
shaft or hole fit. No dependencies, standard library only.

## What it does

Given a nominal size and a tolerance class, for example `22 H7`, it prints:

- the upper / lower deviations in µm,
- the lower and upper limits in mm,
- the tolerance width,
- the GO and NO-GO ends,
- and, when you pass measured values, a verdict per end and overall.

Verdict rules (the same as a gauge inspection sheet):

- **Not OK** — a measured value lies outside the limits.
- **Hati-Hati** — inside, but within 10% of the tolerance width from a limit.
- **OK** — inside and not near a limit.

GO / NO-GO assignment: for a hole (capital letter, e.g. `H7`) GO is the
smaller limit and NO-GO the larger one; for a shaft (lowercase, e.g. `h7`)
it is the other way round.

## Install and run

Python 3.10 or newer. No packages to install.

```sh
python -m iso286 22 H7
python -m iso286 220 F8 --go 220.08 --nogo 220.09
python -m iso286 22 H7 --measure 22.011
python -m iso286 22 H7 --json
python -m iso286 --list-classes
python -m iso286 --list-classes hole
```

Example output:

```
22 H7  (ISO 286-2, nominal over 3 up to 400 mm)
deviations: +21 / 0 µm (upper / lower)
limits:     22 - 22.021 mm
width:      0.021 mm
GO:         22 mm
NO-GO:      22.021 mm
```

Use it as a library too:

```python
from iso286 import limits, go_nogo, verdict

limits(22, "H7")              # (22.0, 22.021)
go_nogo(22, "H7")             # (22.0, 22.021)  GO, NO-GO
verdict(220, "F8", go=220.08, nogo=220.09)  # {'go': 'OK', 'nogo': 'OK', 'overall': 'OK'}
```

## Coverage

- Nominal sizes **over 3 mm up to 400 mm** (the standard size steps).
- **37 shaft classes**: a12, d6, e6, e13, f5, f6, f7, g5, g6, g7, h4–h12,
  j5, j6, j7, js5, js6, js7, k5, k6, k7, m5, m6, m7, n5, n6, n7, p5, p6, r6.
- **35 hole classes**: E6, E7, E11, E12, E13, F6, F7, F8, G6, G7, G8,
  H6–H11, J6, J7, J8, JS6, JS7, JS8, K6, K7, K8, M6, M7, M8, N6, N7, N8,
  P6, P7, P8.

A class outside this list (for example `D10`, `e8`, `f8`) raises an error
instead of guessing a deviation. A nominal size outside 3–400 mm does the
same.

## Data source

The tables in `iso286/tables.json` are the ISO 286-2:2010 limit-deviation
tables, values in micrometres as `[upper, lower]` pairs. The F6/F7/F8 hole
rows follow the fundamental-deviation + IT computation noted in the source
sheet. This tool is not the standard itself: verify against the official
ISO 286-2 tables before using the result for inspection.

## Tests

```sh
python -m unittest discover -s tests -v
```
