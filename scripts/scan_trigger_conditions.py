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
    python scripts/scan_trigger_conditions.py --root /path/to/campaign --only review

Exit status is 1 when a DEFINITE trigger is found and 0 otherwise, so it can gate a merge in
CI or a shell pipeline. Conditional findings are printed but do not fail the run. The
spectrum checks (numerical-core) and the review-GUI checks (PR #58) print their own RESULT
line; ``--only numerical`` / ``--only review`` runs just one of them.

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

Review-GUI checks (PR #58)
--------------------------
The #58 GUI fixes do not change how existing files are processed, but reviews saved with the
old GUI can hold wrong frozen-well counts. These checks find them by comparing each
``reviewed_*.dat`` with the raw ``.dat`` beside it and the logged ``changes`` column. The
fixed GUI never produces either shape, so a hit means the review should be redone:

  erased-freeze  DEFINITE. A -1 started on a row where the count had not risen, and the
                 old walk-back explains it: from March 2025 the GUI used the walk-back
                 *distance* as a row label, so a late -1 started far earlier in the run.
                 The scanner finds the image that was clicked and where the count really
                 rose, and reports the rows in between that lost a frozen well (fixed in
                 c8520b1).
  minus-drop     DEFINITE. A -1 started on the clicked image although the count had not risen
                 there (how the GUI before March 2025 applied every -1), so the saved count
                 drops as temperature falls and the rows between the rise and that image
                 still count the extra well. The raw data has no drop there.
  lost-well      DEFINITE. The saved count is below raw count + logged clicks (clipped to
                 0..wells_per_sample). The old GUI clipped at the cap but logged the click
                 unclipped, so a +1/-1 pair for a late-detected well near a full plate removed
                 a real well (fixed in 8e1de64). A +1 clicked on an image already at the cap
                 is not counted: the fixed GUI refuses it and saves the same count.
  misplaced-harmless  INFO. A reach-back -1 that only crossed rows with no frozen wells, so
                 clipping at 0 left every count as a correct -1 would have.

Limits: a misplaced -1 that happened to start on a rise looks like a correct one, and the
click order is unknown, so the reconstruction ignores the other clicks' effect. A clean
result means "no detectable damage", not "every click went where it was meant". The fixed
GUI's review of a real 16-click run comes out clean; the same clicks through the old GUI are
flagged (tests/test_scripts/test_scan_trigger_conditions.py).
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ERROR_SIGNAL = -9999.0
TOTAL_WELLS = 192  # wells on the plate; wells_per_sample defaults to TOTAL_WELLS // num_samples
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


# --- Review-GUI checks (PR #58) ----------------------------------------------------------


def _net_and_minus(entry: object) -> tuple[int, int]:
    """(net change, minus part) of one sample's ``changes`` entry.

    Reviews before the plus/minus split hold one net number per sample; newer ones hold a
    ``(plus, minus)`` tally. A net number counts as all plus or all minus, as in the GUI.
    """
    if isinstance(entry, tuple | list):
        plus, minus = (int(v) for v in entry)
        return plus + minus, minus
    net = int(entry)  # type: ignore[call-overload]
    return net, min(net, 0)


def _reach_back_click(pre: list[int], start: int, image_rows: list[int]) -> tuple[int, int] | None:
    """Find the click that the old GUI's -1 would have started at ``start``.

    The old -1 walked back from the clicked image row ``c`` to the last row ``i`` (>= 1)
    showing one less, then used the *distance* ``c - i`` as the start row. Returns ``(c, i)``
    for the image row whose walk-back lands on ``start``, so the real rise was at ``i + 1``,
    or None if no image fits (e.g. the -1 came from the pre-March-2025 GUI, which applied
    from the clicked image itself).

    Args:
        pre: counts the researcher saw before this click, by row
        start: row the -1 started on, from the changes column
        image_rows: rows that carry a picture (clicks only happen there)
    """
    last_seen: dict[int, int] = {}
    images = iter(sorted(r for r in image_rows if r > start))
    next_image = next(images, None)
    for row, count in enumerate(pre):
        if row >= 1:
            last_seen[count] = row
        while next_image is not None and next_image == row:
            i = last_seen.get(pre[row] - 1)
            if i is not None and row - i == start:
                return row, i
            next_image = next(images, None)
        if next_image is None:
            break
    return None


def _find_review_damage(
    raw: list[int],
    saved: list[int],
    changes: list[object],
    cap: int,
    image_rows: list[int] | None = None,
) -> list[tuple[str, int, str]]:
    """Rows of one sample whose saved count the fixed review GUI would have saved differently.

    Args:
        raw: frozen-well counts from the raw .dat, by row
        saved: counts in the reviewed .dat, by row
        changes: that sample's entry in the ``changes`` column, by row
        cap: wells_per_sample
        image_rows: rows that carry a picture; without them a misplaced -1 is only caught
            where it left a visible drop

    Returns:
        (kind, row, detail) per finding: "erased-freeze", "minus-drop" and "lost-well" are
        damage; "misplaced-harmless" is a misplaced -1 that only touched an empty plate
    """
    hits: list[tuple[str, int, str]] = []
    nets = [_net_and_minus(c) for c in changes]
    intended = [r + n for r, (n, _) in zip(raw, nets, strict=True)]  # uncapped raw + clicks

    # lost-well: saved below raw + logged clicks, from a +1 the cap swallowed. A +1 clicked on
    # an image that already showed the cap is skipped: the fixed GUI refuses that click and
    # ends up with the same saved count.
    last_plus: int | None = None
    for row in range(len(raw)):
        prev_net, prev_minus = nets[row - 1] if row else (0, 0)
        net, minus = nets[row]
        # a +1 starts here: the plus tally rose, or (old net-only format) the net rose
        if net - minus > prev_net - prev_minus or net > prev_net:
            last_plus = row
        expected = min(max(intended[row], 0), cap)
        if saved[row] >= expected or last_plus is None:
            continue
        shown_before_plus = min(max(intended[last_plus] - 1, 0), cap)
        if shown_before_plus >= cap:
            continue
        hits.append(
            (
                "lost-well",
                row,
                f"saved {saved[row]}, but raw {raw[row]} + logged clicks give {expected}",
            )
        )

    # -1 placement: every row where a -1 starts. A start on an image row was applied at the
    # clicked image itself; a reach-back start is an arbitrary row and almost never an image.
    images = set(image_rows or [])
    for start in range(1, len(raw)):
        net_step = nets[start][0] - nets[start - 1][0]
        minus_step = nets[start][1] - nets[start - 1][1]
        if net_step >= 0 and minus_step >= 0:
            continue
        # what the researcher saw before this -1 (other clicks' order is unknown; ignored)
        pre = [min(max(v + (1 if r >= start else 0), 0), cap) for r, v in enumerate(intended)]
        if pre[start] > pre[start - 1]:
            continue  # starts on a rise, as a correct -1 does
        click = None if start in images else _reach_back_click(pre, start, sorted(images))
        if click is not None:
            clicked, before_rise = click
            wrong = [r for r in range(start, before_rise + 1) if pre[r] >= 1]
            where = f"clicked at row {clicked + 1}, count rose at row {before_rise + 2}"
            if wrong:
                hits.append(
                    (
                        "erased-freeze",
                        start,
                        f"-1 {where} but started at row {start + 1}: {len(wrong)} earlier "
                        f"rows lost a frozen well (e.g. row {wrong[0] + 1}: "
                        f"{pre[wrong[0]]} -> {pre[wrong[0]] - 1})",
                    )
                )
            else:
                hits.append(
                    (
                        "misplaced-harmless",
                        start,
                        f"-1 {where} but started at row {start + 1}; the rows in between "
                        "were 0, so no count changed",
                    )
                )
        elif saved[start] < saved[start - 1] and raw[start] >= raw[start - 1]:
            hits.append(
                (
                    "minus-drop",
                    start,
                    f"a -1 here drops the saved count {saved[start - 1]} -> {saved[start]} "
                    f"(raw {raw[start - 1]} -> {raw[start]}); the rows between the rise and "
                    "this one still count the extra well",
                )
            )
    return hits


@dataclass
class _Dat:
    rows: list[dict[str, str]]
    columns: list[str]


def _read_dat(path: Path) -> _Dat | None:
    """Read a tab-separated OLAF .dat, or None if it is not one (no Sample_ columns)."""
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    reader = csv.reader(io.StringIO(text), delimiter="\t")
    columns = [c.strip() for c in next(reader, [])]
    if not any(c.startswith("Sample_") for c in columns):
        return None
    rows = [dict(zip(columns, r, strict=False)) for r in reader if any(cell.strip() for cell in r)]
    return _Dat(rows=rows, columns=columns)


_REVIEWED_PREFIX = re.compile(r"^(?:.*_)?reviewed_?")
_VERSION_SUFFIX = re.compile(r"\(\d+\)$")


def _raw_partner(reviewed: Path) -> Path | None:
    """The raw .dat a reviewed file was made from, if it sits beside it.

    ``reviewed_X(2).dat``, ``test1_reviewed_X.dat`` and ``reviewed_reviewed_X.dat`` all come
    from ``X.dat`` (a reopened review carries its changes over). The goldens' bare
    ``reviewed.dat`` pairs with ``raw.dat``.
    """
    stem = _VERSION_SUFFIX.sub("", _REVIEWED_PREFIX.sub("", reviewed.stem))
    candidate = reviewed.with_name(f"{stem or 'raw'}.dat")
    return candidate if candidate.exists() and candidate != reviewed else None


_DAMAGE_KINDS = ("erased-freeze", "minus-drop", "lost-well")


@dataclass
class _ReviewResult:
    damage: list[str]
    harmless: list[str]
    reason: str | None = None  # set when the pair could not be checked


def _scan_review(
    reviewed_path: Path, raw_path: Path, wells_per_sample: int | None
) -> _ReviewResult:
    """Findings for one reviewed/raw pair, or the reason it could not be checked."""
    reviewed, raw = _read_dat(reviewed_path), _read_dat(raw_path)
    if reviewed is None or raw is None or "changes" not in reviewed.columns:
        return _ReviewResult([], [], "no Sample_ or changes column")
    if len(reviewed.rows) != len(raw.rows):
        return _ReviewResult(
            [], [], f"row counts differ (reviewed {len(reviewed.rows)}, raw {len(raw.rows)})"
        )
    if "Picture" in reviewed.columns and "Picture" in raw.columns:
        mismatch = sum(
            a.get("Picture", "").strip() != b.get("Picture", "").strip()
            for a, b in zip(reviewed.rows, raw.rows, strict=True)
        )
        if mismatch:
            return _ReviewResult(
                [], [], f"{mismatch} rows show a different picture than the raw file"
            )
    image_rows = [i for i, r in enumerate(reviewed.rows) if r.get("Picture", "").strip()]
    try:
        changes = [ast.literal_eval(r.get("changes", "").strip()) for r in reviewed.rows]
        num_samples = len(changes[0])
        raw_counts = [[int(float(r[f"Sample_{s}"])) for r in raw.rows] for s in range(num_samples)]
        saved_counts = [
            [int(float(r[f"Sample_{s}"])) for r in reviewed.rows] for s in range(num_samples)
        ]
    except (ValueError, SyntaxError, KeyError, TypeError, IndexError) as exc:
        return _ReviewResult([], [], f"could not parse counts or changes ({type(exc).__name__})")
    cap = wells_per_sample or TOTAL_WELLS // num_samples
    highest = max(max(c) for c in saved_counts)
    if highest > cap:
        return _ReviewResult(
            [],
            [],
            f"saved counts reach {highest}, above wells_per_sample={cap}; pass "
            "--wells-per-sample with the run's value",
        )

    result = _ReviewResult([], [])
    for sample in range(num_samples):
        sample_changes = [row[sample] for row in changes]
        hits = _find_review_damage(
            raw_counts[sample], saved_counts[sample], sample_changes, cap, image_rows
        )
        for kind in (*_DAMAGE_KINDS, "misplaced-harmless"):
            of_kind = [(row, detail) for k, row, detail in hits if k == kind]
            if not of_kind:
                continue
            first, detail = of_kind[0]
            temp = reviewed.rows[first].get("Avg_Temp", "?").strip()
            more = f" (+{len(of_kind) - 1} more)" if len(of_kind) > 1 else ""
            entry = (
                f"  [{kind}] {reviewed_path}\n      Sample_{sample}, first at row {first + 1} "
                f"({temp}degC): {detail}{more}"
            )
            (result.harmless if kind == "misplaced-harmless" else result.damage).append(entry)
    return result


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

    # (raw, saved, changes, image rows, expected kinds, label) - one sample each, cap 4
    review_cases: list[tuple[list[int], list[int], list[object], list[int], set[str], str]] = [
        ([0, 0, 1, 1, 2], [0, 0, 0, 0, 1], [0, 0, -1, -1, -1], [2], set(), "-1 at the rise"),
        (
            # clicked row 5 (count 2, rose at row 5); old GUI started at 5 - 4 = row 1
            [0, 0, 0, 1, 1, 2],
            [0, 0, 0, 0, 0, 1],
            [0, -1, -1, -1, -1, -1],
            [4, 5],
            {"erased-freeze"},
            "-1 reached back and erased the first freeze",
        ),
        (
            # clicked row 4 (rose at row 3); old GUI started at 4 - 2 = row 2, still empty
            [0, 0, 0, 1, 1],
            [0, 0, 0, 0, 0],
            [0, 0, -1, -1, -1],
            [3, 4],
            {"misplaced-harmless"},
            "-1 reached back over an empty plate only",
        ),
        (
            [0, 1, 1, 1, 2],
            [0, 1, 1, 0, 1],
            [0, 0, 0, -1, -1],
            [3],
            {"minus-drop"},
            "pre-2025 -1 applied mid-plateau",
        ),
        (
            [3, 3, 4, 4],
            [4, 4, 3, 3],
            [1, 1, 0, 0],
            [0, 2],
            {"lost-well", "minus-drop"},
            "+1/-1 pair at the cap lost a well (old GUI)",
        ),
        (
            [3, 3, 4, 4],
            [4, 4, 4, 4],
            [(1, 0), (1, 0), (1, -1), (1, -1)],
            [0, 2],
            set(),
            "same pair in the fixed GUI",
        ),
    ]
    for raw, saved, changes, images, expected_kinds, label in review_cases:
        got_kinds = {k for k, _, _ in _find_review_damage(raw, saved, changes, 4, images)}
        ok = got_kinds == expected_kinds
        failures += not ok
        print(
            f"  [{'ok ' if ok else 'FAIL'}] {label}: expected {sorted(expected_kinds)}, "
            f"got {sorted(got_kinds)}"
        )
    print("self-test passed" if not failures else f"self-test FAILED ({failures})")
    return 1 if failures else 0


def scan(
    root: Path,
    verbose: bool = False,
    only: str | None = None,
    wells_per_sample: int | None = None,
) -> int:
    status = 0
    if only != "review":
        status |= _scan_numerical(root, verbose)
    if only != "numerical":
        status |= _scan_reviews(root, verbose, wells_per_sample)
    return status


def _scan_reviews(root: Path, verbose: bool, wells_per_sample: int | None) -> int:
    reviewed_files = sorted(
        p
        for p in root.rglob("*.dat")
        if not any(part in _SKIP_DIRS for part in p.parts) and "reviewed" in p.stem
    )
    print("\n" + "=" * 72)
    print("Review-GUI checks (PR #58): reviewed_*.dat saved with the old GUI")
    print("=" * 72)

    damaged: list[str] = []
    harmless: list[str] = []
    unpaired: list[Path] = []
    unchecked: list[str] = []
    checked = 0
    for path in reviewed_files:
        raw = _raw_partner(path)
        if raw is None:
            unpaired.append(path)
            continue
        result = _scan_review(path, raw, wells_per_sample)
        if result.reason is not None:
            unchecked.append(f"  {path}\n      {result.reason}")
            continue
        checked += 1
        damaged.extend(result.damage)
        harmless.extend(result.harmless)
        if verbose:
            print(f"  checked {path}  against {raw.name}  damage={len(result.damage)}")

    print(
        f"\nChecked {checked} of {len(reviewed_files)} reviewed .dat files under {root} "
        "against the raw .dat beside them.\n"
    )
    if damaged:
        print(f"{len(damaged)} finding(s) where the fixed GUI would have saved other counts:\n")
        print("\n".join(damaged))
    else:
        print("No erased-freeze, minus-drop or lost-well damage found.")
    if harmless:
        print(
            f"\n{len(harmless)} misplaced -1 click(s) that changed no count (they only crossed "
            "rows with no\nfrozen wells). Listed for completeness; they do not affect the exit "
            "status.\n"
        )
        print("\n".join(harmless))
    if unpaired:
        print(f"\n{len(unpaired)} reviewed file(s) have no raw .dat beside them (not checked):")
        for p in unpaired:
            print(f"  {p}")
    if unchecked:
        print(f"\n{len(unchecked)} pair(s) could not be checked:")
        print("\n".join(unchecked))

    if damaged:
        files = len({entry.split("\n")[0].split("] ", 1)[1] for entry in damaged})
        print(
            f"\nRESULT (review): {len(damaged)} finding(s) in {files} reviewed file(s). "
            "Re-review these from the\nraw .dat with the fixed GUI and reprocess; their INP/L "
            "values are built on wrong well counts."
        )
        return 1
    print("\nRESULT (review): no detectable review damage in the checked files.")
    return 0


def _scan_numerical(root: Path, verbose: bool) -> int:
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
    parser.add_argument(
        "--only",
        choices=("numerical", "review"),
        help="run only the numerical-core spectrum checks or only the review-GUI checks",
    )
    parser.add_argument(
        "--wells-per-sample",
        type=int,
        help=f"cap for the review checks (default: {TOTAL_WELLS} // number of samples)",
    )
    args = parser.parse_args()

    if args.self_test:
        return _self_test()
    if args.root is None:
        parser.error("--root is required unless --self-test is given")
    if not args.root.exists():
        print(f"error: {args.root} does not exist", file=sys.stderr)
        return 2
    return scan(
        args.root,
        verbose=args.verbose,
        only=args.only,
        wells_per_sample=args.wells_per_sample,
    )


if __name__ == "__main__":
    raise SystemExit(main())
