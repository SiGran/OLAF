# OLAF run configurations

Each OLAF pipeline stage is driven by a `.toml` config file instead of editing the
`main_*.py` scripts. This keeps the scripts untouched and gives you a record of exactly
which inputs produced a given output (a copy of the config is also written into each run's
output folder as `used_config_*.toml`, named after the run's crucial variables, e.g.
`used_config_RAM_CINC_2025-07-16_base.toml`).

## Layout

Configs are organized **by campaign, then by stage**:

```
configs/
  templates/                       # copy these to start a new config
    main.example.toml
    blanks.example.toml
    final_combine.example.toml
  <CAMPAIGN>/                       # e.g. RAM_CINC, CoURAGE
    samples/                        # stage 1 (main.py) - one per treatment-folder
      A12_07.16.25_base.toml
    blanks/                         # stage 2 (main_for_blanks.py)
      blanks.toml
    final_combine/                  # stage 3 (main_final_combine.py)
      final_combine.toml
```

Stage 1 produces many configs (one per experiment/treatment folder), while stages 2 and 3
typically need just one config per campaign.

## Workflow

1. Copy the relevant template into your campaign's stage folder and rename it descriptively.
2. Edit the values. Comments in the templates explain each field.
3. Run the stage, pointing it at your config:

   ```bash
   python -m olaf.main              configs/RAM_CINC/samples/A12_07.16.25_base.toml
   python -m olaf.main_for_blanks   configs/RAM_CINC/blanks/blanks.toml
   python -m olaf.main_final_combine configs/RAM_CINC/final_combine/final_combine.toml
   ```

   If you run a script with no argument, it uses the `DEFAULT_CONFIG` path set near the top
   of that script. A path given on the command line always overrides the default.

   Run these from the repository root.

## Notes

- The `templates/` folder and example campaign are tracked in git. Whether you commit your
  own campaign configs is up to you and your team's provenance needs.
- Relative `project_folder` / `data_folder` paths are resolved from the directory you run
  the script in (typically the repo root).
- The `project_folder` and `data_folder` paths can also be hard-coded to the preferred location`D:/campagins/campaign_x/data`
