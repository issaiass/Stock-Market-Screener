#!/usr/bin/env python3
"""Turn the Markdown premarket report into a clean HTML page.
Usage: python render_report.py REPORT.md [YYYY-MM-DD]
Writes reports/premarket_<date>.html (relative to the current directory).
"""
import html
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown

ET = ZoneInfo("America/New_York")

CSS = """
:root { --bg:#f6f7f9; --card:#fff; --text:#1f2933; --muted:#5f6c7b; --line:#dde2e8; --head:#eef1f5; --zebra:#f8f9fb; --accent:#2f5d8a; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#14181d; --card:#1b2027; --text:#e4e8ec; --muted:#9aa6b2; --line:#2c343d; --head:#232a33; --zebra:#1f252c; --accent:#7fb0e0; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:16px/1.6 Georgia, "Times New Roman", serif; }
header, main, footer { max-width:900px; margin:0 auto; padding:0 16px; }
header { padding-top:32px; padding-bottom:16px; border-bottom:2px solid var(--accent); }
header h1 { margin:0 0 6px; font:700 1.7rem/1.25 system-ui, -apple-system, "Segoe UI", sans-serif; }
header .date { color:var(--muted); font:0.95rem system-ui, sans-serif; }
main { background:var(--card); border:1px solid var(--line); border-top:0; padding-top:8px; padding-bottom:24px; }
h2, h3 { font-family:system-ui, -apple-system, "Segoe UI", sans-serif; line-height:1.3; }
h2 { margin-top:2rem; padding-bottom:.3rem; border-bottom:1px solid var(--line); font-size:1.3rem; }
h3 { color:var(--muted); font-size:1rem; font-weight:600; }
blockquote { margin:1rem 0; padding:.6rem 1rem; border-left:4px solid var(--accent); background:var(--head); color:var(--muted); }
.table-wrap { overflow-x:auto; margin:1rem 0; }
table { border-collapse:collapse; width:100%; font:0.9rem/1.45 system-ui, sans-serif; }
th, td { border:1px solid var(--line); padding:.5rem .65rem; text-align:left; vertical-align:top; }
thead th { background:var(--head); font-weight:600; }
tbody tr:nth-child(even) { background:var(--zebra); }
code { background:var(--head); padding:.1em .35em; border-radius:3px; font-size:.9em; }
pre { background:var(--head); padding:.8rem; overflow-x:auto; border-radius:4px; }
hr { border:0; border-top:1px solid var(--line); margin:2rem 0; }
footer { padding-top:16px; padding-bottom:32px; color:var(--muted); font:0.85rem system-ui, sans-serif; text-align:center; }
"""


# Footer text per language; any other language falls back to English.
FOOTERS = {
    "spanish": ("es", "Generado", "Hecho por Claude Sonnet + Claude Haiku", "Solo con fines educativos, no es asesoría financiera"),
    "english": ("en", "Generated", "Built by Claude Sonnet + Claude Haiku", "Educational only, not financial advice"),
}


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python render_report.py REPORT.md [YYYY-MM-DD]")
    src = Path(sys.argv[1])
    now = datetime.now(ET)
    date = sys.argv[2] if len(sys.argv) > 2 else now.strftime("%Y-%m-%d")
    code, gen, built, disclaimer = FOOTERS.get((sys.argv[3] if len(sys.argv) > 3 else "english").lower(), FOOTERS["english"])
    datetime.strptime(date, "%Y-%m-%d")  # validate

    text = src.read_text(encoding="utf-8")
    m = re.match(r"\s*#\s+(.+)\n", text)  # first H1 becomes the page header
    title = m.group(1).strip() if m else "Premarket Report"
    if m:
        text = text[m.end():]

    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    body = re.sub(r"(<table>.*?</table>)", r'<div class="table-wrap">\1</div>', body, flags=re.S)

    stamp = now.strftime("%Y-%m-%d %H:%M ET")
    page = f"""<!doctype html>
<html lang="{code}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Premarket Report {date}</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1>{html.escape(title)}</h1>
<div class="date">{date}</div>
</header>
<main>
{body}
</main>
<footer>{gen} {stamp} &middot; {built} &middot; {disclaimer}</footer>
</body>
</html>
"""
    out = Path("reports") / f"premarket_{date}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(out.resolve())


if __name__ == "__main__":
    main()
