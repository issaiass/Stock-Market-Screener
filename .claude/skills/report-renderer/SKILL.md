---
name: report-renderer
description: Stage 5.1 of the premarket pipeline. Runs render_report.py to turn the merged Markdown report (REPORT.md) into a clean, readable HTML page at reports/premarket_<date>.html and opens it. Use when the user wants to render, restyle, or open the report as HTML.
---

# Report Renderer

```
.venv\Scripts\python .claude\skills\report-renderer\render_report.py REPORT.md [YYYY-MM-DD]
```

- Converts Markdown with the `markdown` library (`tables`, `fenced_code`, `sane_lists`).
- The report's first H1 becomes the page header, with the date under it. Default date is today in ET.
- Neutral light style, 900px max width, zebra-striped tables with a subtle header row, dark-mode aware, tables scroll sideways on narrow screens.
- Footer: "Generated <time ET> · Built by Claude Sonnet + Claude Haiku · Educational only, not financial advice".
- Output is written to `reports/premarket_<date>.html` under the current directory. Output path is printed.
- To open it on Windows: `start "" reports\premarket_<date>.html`.
