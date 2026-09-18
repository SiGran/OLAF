#!/usr/bin/env python3
"""Scan any OLAF data tree for spectra whose output would differ on the numerical-core branch.

Fixture tests only prove parity on the fixtures. This answers the question they cannot:
*given my actual archive, would any output change?*

It reads CSVs only - the pipeline is never run - so it scales to a full campaign archive in
seconds. Read-only: nothing is written, moved or deleted.

Usage
-----
    python scripts/scan_trigger_conditions.py --root /path/to/campaign
    python scripts/scan_trigger_conditions.py --root tests/test_data --verbose

Exit status is 1 when a DEFINITE trigger is found and 0 otherwise, so it can gate a merge in
CI or a shell pipeline. Conditional findings are printed but do not fail the run.

What it looks for
-----------------
Three of the four observable behavior changes can be detected statically from a spectrum:

  gap-bridge   DEFINITE. A usable row preceded by one or more ERROR_SIGNAL rows, whose
               value is below the last usable value before the gap. The branch corrects it;
               develop kept the physically impossible drop. ERROR_SIGNAL rows are never
               filtered out, so this always reaches the correction logic.
  filename     DEFINITE. An INPs_L file whose stem ends ")" and contains two or more "(".
               On develop this raised NameError or, after the first occurrence in a run,
               wrote the current folder's data to the *previous* folder's output path.
  zero-bridge  CONDITIONAL. The same shape but crossing a zero row. Usually harmless:
               _final_check first drops every row whose *paired original* spectrum is zero,
               which normally removes exactly these rows before the walk-back sees them.
               Verified on the kcg fixture - 6 zero rows, identical output from both
               versions. Reported for review but does not set the exit status, because
               zeros at warm temperatures are ubiquitous and would otherwise cry wolf.

The fourth - an extrapolation that fully covers the missing temperatures, which aborted the
run on develop with a ValueError - depends on the blank/sample temperature ranges at runtime
and cannot be determined from a single file. It is reported as not statically checkable.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

ERROR_SIGNAL = -9999.0
_SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".idea", "_build"}


def _read_spectrum(path: Path) -> tuple[list[float], list[float]] | None:
    """Return (degC, INPS_L) from an OLAF CSV, or None if it is not one.

    Deliberately hand-rolled rather than using olaf.utils so the scanner keeps working on
    legacy files with missing or malformed metadata headers, which are common in archives.
    """
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return None

    header_idx = None
    for i, line in enumerate(lines[:60]):
        cells = [c.strip().lower() for c in next(csv.reader(io.StringIO(line)), [])]
        if "inps_l" in cells:
            header_idx = i
            break
    if header_idx is None:
        return None

    cols = [c.strip().lower() for c in next(csv.reader(io.StringIO(lines[header_idx])))]
    v_idx = cols.index("inps_l")
    t_idx = cols.index("degc") if "degc" in cols else None

    temps: list[float] = []
    values: list[float] = []
    # csv.reader (not str.split) because the dilution column can hold quoted tuples such as
    # "(1,)", whose embedded comma silently corrupted a naive split and dropped whole rows.
    for row in csv.reader(io.StringIO("\n".join(lines[header_idx + 1 :]))):
        if len(row) != len(cols):
            continue
        try:
            values.append(float(row[v_idx]))
            temps.append(float(row[t_idx]) if t_idx is not None else float(len(temps)))
        except (ValueError, IndexError):
            continue
    return (temps, values) if values else None


def _crossable(value: float) -> bool:
    """Values the branch's walk-back steps over: exactly ERROR_SIGNAL and zero.

    NaN is deliberately not crossable - the walk breaks on anything that is neither
    ERROR_SIGNAL nor zero, so it stops at a NaN and ``current < NaN`` is False. Both
    versions leave a NaN gap alone, so reporting one would be a false positive.
    """
    return value == ERROR_SIGNAL or value == 0


def _find_bridges(temps: list[float], values: list[float]) -> list[tuple[str, float, str]]:
    """Locate rows the branch would correct but develop would not.

    Develop compared against the *immediate* predecessor and gave up if it was
    ERROR_SIGNAL or zero, so the versions can only diverge where the immediate predecessor
    is crossable and an earlier non-crossable value exceeds the current one. Kept in sync
    with ``TestParityInputsAreTriggerFree`` in tests/test_integration/test_develop_parity.py.
    """
    hits: list[tuple[str, float, str]] = []
    for i, current in enumerate(values):
        if i == 0 or _crossable(current) or not _crossable(values[i - 1]):
            continue
        j = i - 1
        crossed_error = False
        while j >= 0 and _crossable(values[j]):
            crossed_error = crossed_error or values[j] == ERROR_SIGNAL
            j -= 1
        if j < 0 or not (current < values[j]):
            continue
        kind = "gap-bridge" if crossed_error else "zero-bridge"
        hits.append(
            (
                kind,
                temps[i],
                f"value {current:.6g} rises to {values[j]:.6g} (from {temps[j]}degC)",
            )
        )
    return hits


def _self_test() -> int:
    """Verify the detector still detects - a scanner that cannot fire proves nothing."""
    cases = [
        ([10.0, 50.0, ERROR_SIGNAL, 30.0, 160.0], 1, "gap after ERROR_SIGNAL"),
        ([10.0, 0.0, 5.0], 1, "gap after zero"),
        ([10.0, 50.0, 30.0], 0, "plain drop, both versions agree"),
        ([10.0, 50.0, float("nan"), 30.0], 0, "NaN gap, both versions stop"),
        ([10.0, ERROR_SIGNAL, 60.0], 0, "gap but no drop"),
    ]
    failures = 0
    for values, expected, label in cases:
        got = len(_find_bridges(list(range(len(values))), values))
        status = "ok " if got == expected else "FAIL"
        if got != expected:
            failures += 1
        print(f"  [{status}] {label}: expected {expected}, got {got}")
    print("self-test passed" if not failures else f"self-test FAILED ({failures})")
    return 1 if failures else 0


def scan(root: Path, verbose: bool = False) -> int:
    csv_files = [
        p
        for p in root.rglob("*.csv")
        if not any(part in _SKIP_DIRS for part in p.parts) and not p.name.startswith(".~lock")
    ]

    scanned = 0
    definite: list[str] = []
    conditional: list[str] = []
    filename_hits: list[Path] = []

    for path in sorted(csv_files):
        stem = path.stem
        if stem.endswith(")") and stem.count("(") >= 2 and path.name.startswith("INPs_L"):
            filename_hits.append(path)

        spectrum = _read_spectrum(path)
        if spectrum is None:
            continue
        scanned += 1
        temps, values = spectrum
        for kind, temp, detail in _find_bridges(temps, values):
            entry = f"  [{kind}] {path}\n      at {temp}degC: {detail}"
            (definite if kind == "gap-bridge" else conditional).append(entry)
        if verbose:
            n_err = sum(1 for v in values if v == ERROR_SIGNAL)
            n_zero = sum(1 for v in values if v == 0)
            print(f"  scanned {path}  rows={len(values)} err={n_err} zero={n_zero}")

    print(f"\nScanned {scanned} OLAF spectra in {len(csv_files)} CSV files under {root}\n")

    if definite:
        print(f"{len(definite)} row(s) WILL be corrected by this branch (ERROR_SIGNAL gap):\n")
        print("\n".join(definite))
    else:
        print("No ERROR_SIGNAL gap-bridge trigger found.")

    if conditional:
        print(
            f"\n{len(conditional)} row(s) sit on a zero-bridge shape. These usually do NOT "
            "differ:\n_final_check drops rows whose paired original spectrum is zero before "
            "the walk-back\nruns. Listed for review only; they do not affect the exit "
            "status.\n"
        )
        print("\n".join(conditional))

    if filename_hits:
        print(f"\n{len(filename_hits)} file(s) with a multi-parenthesis name:\n")
        for p in filename_hits:
            print(f"  [filename] {p}")
    else:
        print("No multi-parenthesis INPs_L filenames found.")

    print(
        "\nNot statically checkable: an extrapolation that fully covers the missing "
        "temperatures\n(develop aborted the run with ValueError; the branch completes). "
        "It depends on the\nblank and sample temperature ranges at runtime."
    )

    total = len(definite) + len(filename_hits)
    if total == 0:
        note = (
            f" ({len(conditional)} conditional finding(s) above are informational)"
            if conditional
            else ""
        )
        print(
            "\nRESULT: no definite triggers. develop and numerical-core produce identical "
            f"output on this data{note}."
        )
        return 0
    print(
        f"\nRESULT: {total} definite trigger(s). Output WILL differ here - review each with "
        "a scientist.\nEvery listed change is a correction develop failed to make, not a "
        "regression."
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find spectra whose output differs between develop and numerical-core.",
    )
    parser.add_argument("--root", type=Path, help="data tree to scan")
    parser.add_argument("--verbose", action="store_true", help="list every file scanned")
    parser.add_argument(
        "--self-test", action="store_true", help="check the detector against planted cases"
    )
    args = parser.parse_args()

    if args.self_test:
        return _self_test()
    if args.root is None:
        parser.error("--root is required unless --self-test is given")
    if not args.root.exists():
        print(f"error: {args.root} does not exist", file=sys.stderr)
        return 2
    return scan(args.root, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
