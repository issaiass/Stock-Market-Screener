#!/usr/bin/env python3
"""Run the full premarket pipeline end to end.
  1 scan.py            -> packet.json
  2 Claude Sonnet      -> sonnet_view.md   (prompt_sonnet.md + packet)
  3 Claude Haiku       -> haiku_view.md    (prompt_haiku.md + packet, blind, separate process)
  4 merge editor       -> REPORT.md        (prompt_merge.md + packet + both views + template)
  5 render_report.py   -> reports/premarket_<date>.html
  6 deliver.py         -> email / Telegram / Discord (channels with keys set)
Usage: python run_pipeline.py [--prompt "focus text"] [--tickers NVDA,AMD] [--effort low|analyst=high,second=low]
       [--lang spanish|english|<any language>] [--send email,telegram,discord|all|none]
       [--cleanup true|false] [--skip-deliver] [--dry-run]
  --lang     language of the report, default spanish. Section titles and text are translated; tickers,
             numbers and original news headlines are kept as they are.
  --cleanup  default true: after a successful run, delete intermediates (packet.json, both views, REPORT.md,
             sandbox, caches). The dated HTML in reports/ and the log are kept. A failed run keeps everything.
  --prompt   guides the analysis for this run only (sector, ticker or instrument), added to all 3 AI prompts
  --tickers  comma list added to the packet with full data even if they did not gap
Run from anywhere: paths resolve from the project root. Logs go to logs/pipeline_<date>.log.
"""
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
SK = ROOT / ".claude" / "skills"
PY = next((p for p in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python") if p.exists()),
          Path(sys.executable))  # Windows venv, Linux/macOS venv, else current interpreter
ET = ZoneInfo("America/New_York")
NOW = datetime.now(ET)
DATE = NOW.strftime("%Y-%m-%d")
LOG = ROOT / "logs" / f"pipeline_{DATE}.log"
CLAUDE_TIMEOUT = 900  # seconds per AI step
ISO = ROOT / ".ai_sandbox"  # empty working dir for claude -p calls
MODELS = {"analyst": "sonnet", "second": "haiku", "merge": "sonnet"}  # claude -p --model aliases
EFFORTS = {"analyst": "low", "second": "low", "merge": "low"}  # claude -p --effort, change with --effort
LEVELS = ("low", "medium", "high", "xhigh", "max")


def log(msg):
    line = f"[{datetime.now(ET):%H:%M:%S}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", **kw)


def ask_claude(prompt, role):
    """Non-interactive Claude Code call. Prompt goes in on stdin."""
    # Isolated: no tools, no skills, neutral cwd. Otherwise the model can see this project's skills and
    # re-launch the pipeline (recursion) or read other files, which would also break the blind second pass.
    ISO.mkdir(exist_ok=True)
    r = subprocess.run(["claude", "-p", "--model", MODELS[role], "--effort", EFFORTS[role], "--disable-slash-commands", "--tools", ""], cwd=ISO, input=prompt,
                       capture_output=True, text=True, encoding="utf-8", timeout=CLAUDE_TIMEOUT)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"claude -p failed: {r.stderr.strip()[:300] or 'empty output'}")
    return r.stdout.strip()


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def clean_markdown(text):
    """Drop code fences or chatter around the report."""
    text = re.sub(r"^```(?:markdown|md)?\s*\n|\n```\s*$", "", text.strip())
    i = text.find("# ")
    return text[i:] if i > 0 and text[:i].strip() else text


def validate(md, tickers):
    """Cheap code checks on the merged report. Returns a list of problems (empty = ok)."""
    problems = []
    if not md.lstrip().startswith("# "):
        problems.append("it must start with the H1 title line")
    if len(re.findall(r"^## ", md, re.M)) < 10:
        problems.append("fewer than 10 '##' sections: all sections of the structure are required")
    if chr(0x2014) in md:  # em dash
        problems.append("it contains em dashes: use commas, periods or colons instead")
    if "<!--PICKS" not in md:
        problems.append("the last line must be the <!--PICKS [...] --> comment")
    seen = {m.group(1) for m in re.finditer(r"^\|\s*\**([A-Z][A-Z0-9.\-]{0,5})\**\s*(?:\([^)]*\))?\s*\|", md, re.M)}
    bad = sorted(seen - tickers)
    if bad:
        problems.append(f"tickers in tables that are not in packet.json: {bad}")
    return problems


def extract_picks(md):
    """Pull the <!--PICKS [...] --> comment out of the report. Returns (report without it, picks list)."""
    m = re.search(r"<!--\s*PICKS\s*(\[.*?\])\s*-->", md, re.S)
    if not m:
        return md, []
    try:
        picks = json.loads(m.group(1))
    except ValueError:
        picks = []
    return (md[:m.start()] + md[m.end():]).rstrip() + "\n", picks


def log_picks(picks, packet):
    """Append picks with their plan numbers to logs/picks_log.csv, for the pick-scorer skill."""
    by = {g["ticker"]: g for g in packet.get("gappers", [])}
    path = ROOT / "logs" / "picks_log.csv"
    path.parent.mkdir(exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "ticker", "list", "conviction", "price", "trigger", "stop", "target_1r", "target_2r"])
        for p in picks:
            g = by.get(p.get("ticker"), {})
            pl = g.get("plan") or {}
            w.writerow([DATE, p.get("ticker"), p.get("list"), p.get("conviction"), g.get("price"),
                        pl.get("trigger"), pl.get("stop"), pl.get("target_1r"), pl.get("target_2r")])
    log(f"logged {len(picks)} picks to logs/picks_log.csv")


def step(name, fn):
    log(f"START {name}")
    fn()
    log(f"DONE  {name}")


def flag_value(name):
    """Value after a --flag, or None."""
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return sys.argv[i + 1].strip()
        sys.exit(f"{name} needs a value")
    return None


def cleanup_generated():
    """Delete intermediates that are not needed to start the app again. Keeps reports/ and logs/."""
    import shutil
    removed = []
    for name in ("packet.json", "sonnet_view.md", "haiku_view.md", "REPORT.md", ".econ_cache.json"):
        p = ROOT / name
        if p.exists():
            p.unlink()
            removed.append(name)
    for d in [ISO] + [p for p in SK.rglob("__pycache__")]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            removed.append(str(d.relative_to(ROOT)))
    log("cleanup removed: " + (", ".join(removed) or "nothing"))


def set_efforts(spec):
    """--effort high  (all steps)  or  --effort analyst=high,second=low,merge=medium"""
    if not spec:
        return
    for part in spec.split(","):
        role, _, level = part.rpartition("=")
        level = level.strip().lower()
        if level not in LEVELS or (role and role.strip() not in EFFORTS):
            sys.exit(f"bad --effort '{part}': levels {LEVELS}, steps {tuple(EFFORTS)}")
        for r in ([role.strip()] if role else list(EFFORTS)):
            EFFORTS[r] = level


def main():
    skip_deliver = "--skip-deliver" in sys.argv
    send = (flag_value("--send") or "all").lower().replace(" ", "")
    channels = {"email", "telegram", "discord"}
    if send == "none":
        skip_deliver = True
    elif send != "all" and not set(send.split(",")) <= channels:
        sys.exit("--send takes all, none, or a comma list of: email, telegram, discord")
    user_prompt, tickers = flag_value("--prompt"), flag_value("--tickers")
    lang = (flag_value("--lang") or "spanish").strip()
    lang_note = (f"\n\n## Language (final report only)\nWrite the entire report in {lang}: all text, section titles, table column "
                 f"headers and the date line (localize the weekday and month). Keep emojis, tickers, numbers, "
                 f"price levels and conviction colors unchanged. Keep news headlines in their original wording "
                 f"(add a short {lang} gloss in parentheses if the headline is in another language).\n")
    set_efforts(flag_value("--effort"))
    cleanup = (flag_value("--cleanup") or "true").lower()
    if cleanup not in ("true", "false", "yes", "no", "1", "0"):
        sys.exit("--cleanup takes true or false")
    cleanup = cleanup in ("true", "yes", "1")
    focus = ("\n\n## Extra focus for this run (from the user)\n" + user_prompt +
             "\nGuide the analysis toward this, using only packet data. Names flagged \"focus\": true in the "
             "packet were requested by the user. If the packet lacks the data to answer part of this, say so "
             "plainly. Never invent catalysts, numbers or headlines.\n") if user_prompt else ""
    if "--dry-run" in sys.argv:
        if user_prompt or tickers:
            print("focus prompt:", user_prompt, "| extra tickers:", tickers)
        print("models:", MODELS, "| efforts:", EFFORTS, "| cleanup:", cleanup, "| lang:", lang, "| send:", send, "(skip)" if skip_deliver else "")
        for s in ("scan", "sonnet analyst", "haiku second brain", "merge", "render", "deliver"):
            print("would run:", s)
        print("root:", ROOT, "| python:", PY, "| date:", DATE)
        return 0

    log(f"pipeline start {NOW:%Y-%m-%d %H:%M} ET")
    if user_prompt or tickers:
        log(f"focus prompt: {user_prompt!r} | extra tickers: {tickers}")
    try:
        def scan():
            cmd = [str(PY), str(SK / "premarket-gatherer" / "scan.py"), "packet.json"]
            r = run(cmd + (["--tickers", tickers] if tickers else []), timeout=1500)
            if r.returncode != 0 or not (ROOT / "packet.json").exists():
                raise RuntimeError(f"scan failed: {r.stderr.strip()[-300:]}")

        template = (SK / "report-template" / "REPORT_TEMPLATE.md").read_text(encoding="utf-8")
        example = (SK / "report-template" / "EXAMPLE_REPORT.md").read_text(encoding="utf-8")
        example_block = "\n\n=== EXAMPLE (fictional content, copy the structure and tone only) ===\n" + example

        # Analyst and second brain always reason in English; only the merge step uses --lang.
        def analyst():
            (ROOT / "sonnet_view.md").write_text(ask_claude(
                read("prompt_sonnet.md") + focus + "\n\n=== INPUT: packet.json ===\n" + read("packet.json")
                + "\n\n=== TEMPLATE: REPORT_TEMPLATE.md ===\n" + template + example_block
                + "\n\nOutput only the finished markdown report.", "analyst"), encoding="utf-8")

        def second():  # blind: sees only its prompt and packet.json
            (ROOT / "haiku_view.md").write_text(ask_claude(
                read("prompt_haiku.md") + focus + "\n\n=== INPUT: packet.json ===\n" + read("packet.json"), "second"),
                encoding="utf-8")

        def merge():
            stamp = NOW.strftime("%A, %B %d, %Y · %I:%M %p ET")
            packet = json.loads(read("packet.json"))
            tickers = {g["ticker"] for g in packet.get("gappers", [])}
            base = (read("prompt_merge.md") + focus + lang_note + f"\n\nStamp the date line with: {stamp}\n"
                    "Sonnet is the analyst pass and Haiku is the second pass (both Claude models).\n"
                    "Output only the finished REPORT.md markdown, starting with the H1.\n\n"
                    "=== INPUT 1: packet.json ===\n" + read("packet.json")
                    + "\n\n=== INPUT 2: sonnet_view.md ===\n" + read("sonnet_view.md")
                    + "\n\n=== INPUT 3: haiku_view.md ===\n" + read("haiku_view.md")
                    + "\n\n=== TEMPLATE: REPORT_TEMPLATE.md ===\n" + template + example_block)
            md = clean_markdown(ask_claude(base, "merge"))
            problems = validate(md, tickers)
            if problems:  # one retry with the problems listed
                log("validation failed, retrying merge once: " + "; ".join(problems))
                md = clean_markdown(ask_claude(
                    base + "\n\n=== FIX THESE PROBLEMS IN YOUR PREVIOUS OUTPUT ===\n- " + "\n- ".join(problems)
                    + "\n\nOutput the corrected full report only.", "merge"))
                problems = validate(md, tickers)
                if problems:
                    log("WARNING report still has problems: " + "; ".join(problems))
            md, picks = extract_picks(md)
            (ROOT / "REPORT.md").write_text(md, encoding="utf-8")
            log_picks(picks, packet)

        def render():
            r = run([str(PY), str(SK / "report-renderer" / "render_report.py"), "REPORT.md", DATE, lang])
            if r.returncode != 0:
                raise RuntimeError(f"render failed: {r.stderr.strip()[-300:]}")

        def deliver():
            r = run([str(PY), str(SK / "report-delivery" / "deliver.py"),
                     f"reports/premarket_{DATE}.html", "REPORT.md"] + ([] if send == "all" else ["--only", send]))
            for line in r.stdout.splitlines():
                log("  " + line)

        for name, fn in (("scan", scan), ("sonnet analyst", analyst), ("haiku second brain", second),
                         ("merge", merge), ("render", render)):
            step(name, fn)
        if skip_deliver:
            log("delivery skipped (--skip-deliver)")
        else:
            step("deliver", deliver)
    except Exception as e:
        log(f"PIPELINE FAILED: {type(e).__name__}: {e}")
        return 1
    if cleanup:
        cleanup_generated()
    log(f"pipeline done: reports/premarket_{DATE}.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
