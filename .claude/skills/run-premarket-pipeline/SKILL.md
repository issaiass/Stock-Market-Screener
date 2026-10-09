---
name: run-premarket-pipeline
description: Stage 6 of the premarket pipeline. Runs the whole chain in one command (scan, Claude Sonnet analyst, blind Claude Haiku second brain, merge, render HTML, deliver) and shows how to schedule it every weekday morning with Windows Task Scheduler. Use when the user wants to run the full premarket report end to end or put it on a schedule.
---

# Run the Premarket Pipeline

One command runs every stage in order:

| # | Stage | Output |
|---|---|---|
| 1 | `premarket-gatherer/scan.py` | `packet.json` |
| 2 | Claude Sonnet analyst (`prompt_sonnet.md` + packet + template) | `sonnet_view.md` |
| 3 | Blind second brain, Claude Haiku (`prompt_haiku.md` + packet only, separate process) | `haiku_view.md` |
| 4 | Merge editor (`prompt_merge.md` + packet + both views + template) | `REPORT.md` |
| 5 | `report-renderer/render_report.py` | `reports/premarket_<date>.html` |
| 6 | `report-delivery/deliver.py` | email / Telegram / Discord (channels with keys set) |

```
.venv\Scripts\python .claude\skills\run-premarket-pipeline\run_pipeline.py
```

Flags: `--prompt "text"` (steer the analysis, this run only), `--tickers A,B` (add names to the packet even if they did not gap), `--effort low|medium|high|xhigh|max` or `analyst=high,second=low,merge=medium` (reasoning effort per step, default low for all), `--lang spanish|english|<any language>` (report language, default spanish), `--cleanup true|false` (default true: delete intermediates after a successful run; keeps `reports/` and `logs/`; failed runs keep everything), `--skip-deliver` (build the report, send nothing), `--dry-run` (print the plan only).

Behavior:
- Paths resolve from the project root, so it runs from any folder. The venv Python is used if `.venv` exists.
- Steps 2 to 4 call `claude -p` (Claude Code CLI, non-interactive) with `--model sonnet` (analyst), `--model haiku` (second brain) and `--model sonnet` (merge). Change the models in the `MODELS` dict in `run_pipeline.py`. Each is a real, billed run, with a 15 minute timeout per step.
- The `claude -p` calls are isolated (`--tools ""`, `--disable-slash-commands`, empty `.ai_sandbox` working dir). Without that, a first test run let the model see this project's skills and re-launch the pipeline recursively, and it would also have broken the blind second pass.
- Any failed step stops the run, logs `PIPELINE FAILED`, and exits 1 so nothing stale gets sent. Delivery channels never crash the run.
- Logs go to `logs/pipeline_<date>.log`.
- With the default `--cleanup true`, a successful run deletes `packet.json`, both views, `REPORT.md`, the econ cache, the sandbox and `__pycache__`. The dated HTML in `reports/` and the log stay. Use `--cleanup false` to keep the intermediates for inspection.

## Scheduler files (in this folder)

- `schedule_windows.ps1`: `.\schedule_windows.ps1 [-TimeET 08:15] [-Remove]`. Converts the Eastern time to the PC's local zone when it registers the task (weekdays, wake to run, start when available).
- `schedule_linux.sh`: `./schedule_linux.sh [08:15 | --remove]`. Installs a weekday cron entry with `CRON_TZ=America/New_York` and logs to `logs/cron.log`.

- `unschedule_windows.ps1` and `unschedule_linux.sh`: standalone removers. They delete only the scheduled task or the tagged cron entry, say so if nothing is scheduled, and leave reports, logs and `.env` alone.

Both are syntax-checked, but neither has been installed on a real schedule. On Windows, DST can shift the local time if the PC is not on US Eastern, so re-run the script after a clock change.

## Schedule it by hand (Windows Task Scheduler)

Run about 8:15 AM ET on weekdays so the report lands before 8:45 AM ET. The task uses the PC's local time, so convert 8:15 ET to local time if the PC is not on Eastern. The PC must be on and awake, and `claude` must be on the PATH of the task's user.

```
schtasks /Create /TN "PremarketPipeline" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:15 ^
  /TR "C:\Users\Denys\Downloads\trading-tools\.venv\Scripts\python.exe C:\Users\Denys\Downloads\trading-tools\.claude\skills\run-premarket-pipeline\run_pipeline.py"
```

Check, test and remove:

```
schtasks /Run /TN "PremarketPipeline"
schtasks /Query /TN "PremarketPipeline" /V /FO LIST
schtasks /Delete /TN "PremarketPipeline" /F
```

If the task runs but nothing arrives, read `logs\pipeline_<date>.log` first.

## Caveats

- Yahoo data is free and may be delayed. Run after 4:00 AM ET or premarket fields will be empty.
- Check `.env` has your delivery keys, or the last stage will just print "skipped" lines.
- Educational only, not financial advice.

## Quality features

- **Language hybrid:** `--lang` applies only to the merge step. The analyst and second brain reason in English; the merge editor writes the final report in the chosen language.
- **Gold-standard example:** `report-template/EXAMPLE_REPORT.md` is included in the analyst and merge prompts.
- **Skeptic second brain:** `prompt_haiku.md` asks Haiku to find why each pick fails.
- **Validation and one retry:** after the merge, the report is checked in code (all sections present, no em dashes, every table ticker exists in the packet, picks block present). On failure the merge is retried once with the problems listed; if it still fails, a warning is logged and the run continues.
- **Pick log:** each run appends to `logs/picks_log.csv`. Score them later with the `pick-scorer` skill.
- Effort stays `low` unless you pass `--effort`.

## Tested (quality features)

One full run (`--skip-deliver --cleanup false`, default Spanish, low effort) passed all stages: analyst and second brain in English, final report in Spanish, validation passed on the first try (no retry needed), the PICKS comment was stripped from `REPORT.md` and 3 picks were logged. Not yet exercised: the validation retry path, the Alpaca premarket RVOL path (needs keys), and `score_picks.py` on real logged picks (only on synthetic rows).

## Scheduling with flags

`schedule_windows.ps1 -PipelineArgs '<flags>'` and `schedule_linux.sh <HH:MM> <flags>` save any `run_pipeline.py` flags into the scheduled command (`--prompt`, `--tickers`, `--lang`, `--effort`, `--cleanup`, `--skip-deliver`). Re-run the install command to change them. Without flags a scheduled run uses the default prompts, Spanish and low effort. Flag passing is syntax-checked and the cron quoting was tested; the Windows task itself was not registered.

`--send all|none|email,telegram,discord` chooses the delivery channels for a run (default all configured). `none` is the same as `--skip-deliver`. It can also be saved into a schedule through the scheduler pass-through.
