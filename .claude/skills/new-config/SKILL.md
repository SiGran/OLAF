---
name: new-config
description: Scaffold a new OLAF pipeline config `.toml` for a given campaign and stage by copying the matching template into configs/<CAMPAIGN>/<stage>/ and filling in the fields the user provides. Use when the user says "new config", "scaffold a config", "set up a run for <campaign>", "add a stage-1/blank/final-combine config", or invokes /new-config.
---

# /new-config — scaffold an OLAF run config

You are creating a new `.toml` config for one OLAF pipeline stage by copying the correct
template and editing values — you are **not** running the pipeline (that is `/check`-adjacent
work, and running a stage is a separate explicit ask). The config-driven architecture is
documented in `configs/README.md` and `CLAUDE.md`; this skill layers the mechanics on top.

## Hard rules (from CLAUDE.md)

- **Never delete files.** Do not overwrite an existing config without the user's say-so. If a
  target path already exists, stop and report it — offer to write alongside (e.g. `<name>.new.toml`)
  and add a "Human-Needs-To-Do" checkbox in `TODO.md` for any rename/removal.
- **Never edit the `main_*.py` scripts** to carry per-run inputs. Everything the user gives you
  goes into the `.toml`. If they ask for an input that has no field yet, that is a model change —
  hand off to the `science-reviewer` mental model / add it to `olaf/config/models.py` **and** the
  matching template (see CLAUDE.md "Working with Main Scripts"), don't invent an undocumented key.
- The pydantic models use `extra="forbid"` — an unknown key will hard-fail at load. Only write keys
  that exist on the target model.

## Step 1 — Identify stage, campaign, and template

Ask only if you cannot infer them. Map stage → template → destination folder:

| Stage | Template | Destination | Model (`olaf/config/models.py`) |
|-------|----------|-------------|-------------------------------|
| 1 (process) | `configs/templates/main.example.toml` | `configs/<CAMPAIGN>/process/` | `MainConfig` |
| 2 (blanks) | `configs/templates/blanks.example.toml` | `configs/<CAMPAIGN>/blanks/` | `BlankConfig` |
| 3 (final combine) | `configs/templates/final_combine.example.toml` | `configs/<CAMPAIGN>/final_combine/` | `FinalCombineConfig` |

Read the template file at scaffold time — do not reproduce it from memory, the fields drift.
Read the matching model class to confirm required vs. defaulted fields before you fill anything in.

## Step 2 — Name the file

- Stage 1: `<sample>_<MM.DD.YY>_<treatment>.toml` (e.g. `A12_07.16.25_base.toml`). One per
  experiment/treatment folder.
- Stage 2: `blanks.toml`. Stage 3: `final_combine.toml`. Usually one per campaign.

If the campaign/stage folder doesn't exist yet, create it (creating directories is allowed;
deleting is not).

## Step 3 — Fill the values

- Copy the template verbatim, then replace only the values the user supplied. Leave the
  explanatory comments intact.
- TOML specifics that bite: strings must be quoted, numbers/booleans are bare, and an
  undiluted/background sample uses bare `inf` (not `"inf"`).
- Stage 1 invariants worth checking before you write (the model only *warns*, so catch them now):
  - `num_samples * wells_per_sample == 192`
  - each `treatment` string should appear in `data_folder`'s name
  - `start_time`/`end_time` are UTC, `"YYYY-MM-DD HH:MM:SS"`, and the date matches the
    `MM.DD.YY` in the folder name
  - `proportion_filter_used` is in `[0, 1]`
- Leave any field you don't have a value for at its template default and say so in your report;
  don't guess scientific inputs (dilutions, volumes, altitudes).

## Step 4 — Validate it loads

Confirm the file parses and passes pydantic validation before declaring success:

```bash
uv run python -c "from olaf.config import load_config, MainConfig; print(load_config('configs/<CAMPAIGN>/<stage>/<file>.toml', MainConfig))"
```

Swap `MainConfig` for `BlankConfig` / `FinalCombineConfig` as appropriate. If loading raises,
fix the config and re-run — a `ValidationError` here is exactly what you're preventing the user
from hitting at run time. Surface (but don't try to silence) any `warnings.warn` output — those
are the soft sanity checks and the user may want to know.

## Step 5 — Report

Tell the user:

- The path written and which template it came from.
- Any field left at its default because you had no value (so they can fill it in).
- Any soft warning the model emitted, verbatim.
- The exact command to run the stage, e.g.
  `python -m olaf.main configs/<CAMPAIGN>/process/<file>.toml`.

Do not run the pipeline yourself unless the user explicitly asks — stage 1 opens a Tkinter GUI
and needs a `$DISPLAY`.
