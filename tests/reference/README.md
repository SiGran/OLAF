# Vendored reference engines (do not edit, do not import from `olaf/`)

Verbatim snapshots of the two scientific engines as they stood on `develop` at commit
**`70f3845`** ("feat: drive pipeline stages from TOML config files (#48)"), taken on
2026-09-17:

- `develop_blank_correction.py` ← `olaf/processing/blank_correction.py`
- `develop_graph_data_csv.py` ← `olaf/processing/graph_data_csv.py`

Regenerate with:

```bash
git show 70f3845:olaf/processing/blank_correction.py > tests/reference/develop_blank_correction.py
git show 70f3845:olaf/processing/graph_data_csv.py   > tests/reference/develop_graph_data_csv.py
```

## Why these exist

`tests/test_integration/test_develop_differential.py` runs the current engines and these
reference engines over the same generated inputs and asserts they agree, except where the
`numerical-core` branch deliberately changed behavior. That is the only protection we have
against differences in data nobody has looked at — fixture tests only prove parity on the
fixtures.

Loading a snapshot is preferable to `git show origin/develop:...` at test time because
GitHub Actions checks out at `fetch-depth: 1`, so `origin/develop` may not exist in CI.

These files import `olaf.CONSTANTS` and `olaf.utils`, which the branch does not modify, so
running them against the current utilities is faithful.

## Rules

- **Never** import these from `olaf/`. They are test-only reference material.
- **Never** hand-edit them. They are a historical pin; editing destroys their only purpose.
- They are excluded from `ruff` in `pyproject.toml` so formatter drift cannot silently
  alter the snapshot.

## Retirement

Once `numerical-core` merges into `develop`, these stop describing "the other side" and
become an ordinary historical copy. Either refresh them against the new baseline before the
next engine change, or remove the snapshot together with the differential test. Tracked in
`TODO.md` under Human-Needs-To-Do.
