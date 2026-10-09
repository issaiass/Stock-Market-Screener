---
name: pnl-dashboard
description: Turn a broker trade CSV into a single self-contained, offline, dark-theme HTML P&L dashboard. Use when the user wants their trades connected to market data (yfinance or their market data API) to profile their edge and see KPIs, weekly equity curve, daily calendar, breakdowns, best/worst stocks, winners-vs-losers profile, hidden leaks, and focus/avoid screens in one HTML file.
---

# P&L Dashboard

Build one HTML file (`pnl_dashboard.html` in the working directory) from the user's broker CSV, enriched with market data. Compute in Python; the HTML embeds the data as JSON and draws everything with inline SVG + vanilla JS. **No external libraries, fonts, CDNs or network calls**, so it works offline.

Load the `dataviz` skill before writing any chart code and follow its palette/accessibility rules (adapted to the dark theme below).

## Pipeline

### 1. Trades (reuse earlier work)
Follow the `pnl-audit` skill's Steps 1-3: file check, reconcile to the broker's realized P&L, rebuild completed round trips (scaled fills = ONE trade, open positions excluded). Reuse a saved `pnl_audit.py` or trades table if present. If reconciliation fails, still build, but show an **UNRECONCILED** banner with the gap on the dashboard.

### 2. Market data
- Check for a configured market data API first (env vars / config in the working directory such as `POLYGON_API_KEY`, `ALPACA_*`, `FMP_API_KEY`, `.env`, `config.*`). If one exists, use it; otherwise use `yfinance` (`pip install yfinance pandas`). State which source was used.
- For every traded symbol, fetch daily OHLCV from ~1 year before the first entry to the last exit, plus SPY and ^VIX. Cache to disk (e.g. `.cache/`) so reruns are fast. Delisted/missing symbols: mark "n/a", list them, exclude from the edge profile only.
- Per trade, as of the **entry date** (no look-ahead; use data through the prior close where the entry-day bar would leak): price, gap %, RSI(14), ATR% and ADR% (20d), price vs 20/50/200 SMA, distance from 52-week high, relative volume (entry-day volume vs 20d average), avg dollar volume, market cap / float / sector (from `Ticker.info`, noting these are current values, not historical), earnings within +/-1 day.
- **Regime** per trade (entry date): SPY above/below its 200-day SMA, and VIX bucket (<15, 15-20, 20-30, >30). Provide a combined label such as "Bull / low-vol".

### 3. Analysis (all numbers computed in code)
Standard stat block per cut: trades, total P&L, win rate, avg win, avg loss, profit factor, expectancy per trade. Flag buckets with <20 trades as low-sample.
- KPIs: total realized P&L, win rate, profit factor, expectancy, max drawdown ($ with peak/trough dates)
- Weekly cumulative equity curve (week = ISO week of exit date; running sum of realized P&L; mark the drawdown span)
- Daily P&L calendar (green/red days, streaks)
- Breakdowns: holding period (same-day / overnight / multi-day), entry weekday, entry time (ET: 9:30-10, 10-11, 11-14, after 14), regime
- Best/worst stocks by total P&L
- Winners-vs-losers edge profile: median of each feature for the top ~15 winners vs top ~15 losers, plus % of each group meeting a condition
- Hidden leaks: 3-5 conditions with consistent losses ($, trades, win rate, expectancy), ranked by dollars lost; say how many combinations were tested
- Focus / avoid screens: concrete ranges from the edge profile (price, ADR, RVOL, float, sector, RSI, trend, regime), phrased as filters usable in Finviz/TradingView

### 4. HTML dashboard (single file)
Embed data as a `<script>const DATA = {...}</script>` block. Everything else is inline CSS/JS/SVG.

Layout, top to bottom, each chart/table in a card **with a one-line takeaway beneath it** generated from the numbers (computed, not hard-coded, e.g. "Same-day trades make +$X while multi-day trades lose $Y"):
1. Header: file, date range, trade count, data source, reconciliation status
2. KPI tiles: P&L, win rate, profit factor, expectancy, max drawdown
3. Weekly cumulative equity curve (line/area, drawdown span shaded)
4. Daily performance calendar (heatmap grid by week x weekday, green/red intensity by P&L)
5. Breakdown bar charts: holding period, day of week, entry time, regime (each showing P&L, with win rate / PF / expectancy / n in tooltip)
6. Best & worst stocks (horizontal bars)
7. Winners-vs-losers edge profile (paired bars or table with feature medians)
8. Hidden leaks (ranked list with $ amounts)
9. Focus / avoid screens (two panels)
10. Footer: methodology, sample-size caveats, "analysis of past data, not financial advice"

Requirements:
- **Dark theme** via CSS variables on `:root`; explicit body background; green for gains, red for losses with a non-color cue too (sign, +/- label) for accessibility
- **Hover tooltips** on every mark (bars, calendar cells, equity points): one shared absolutely-positioned tooltip div, shown with mouse and keyboard focus; tooltip shows the date/label, P&L, trades, win rate, PF, expectancy as relevant
- Responsive: cards in a CSS grid; works at phone width, no horizontal page scroll; charts are SVG with `viewBox` so they scale
- No external resources of any kind (no `<script src>`, no `<link>`, no web fonts, no images by URL); verify with a grep for `http` in the output (only allowed inside text such as footnotes)
- Low-sample buckets visibly marked (e.g. hatched bar or "n=7" label)
- Empty/missing data renders "n/a", never a broken chart

### 5. Verify before reporting
- Reconciliation status shown and numbers on the dashboard match the computed tables (spot check totals: sum of buckets = overall)
- Open the HTML (or parse it) to confirm it renders with no console errors; if a browser tool is available, screenshot it and check dark theme, tooltips, and mobile width
- Confirm offline: grep for external URLs and for `fetch(`/`XMLHttpRequest`

## Output

Tell the user: the path of `pnl_dashboard.html`, the saved script (e.g. `build_dashboard.py`) to regenerate it, the data source used, reconciliation status, symbols with missing data, and 3 headline findings. Don't publish or upload the dashboard anywhere; it contains the user's personal trading data.

## Rules

- Never fabricate numbers; mark unavailable values "n/a".
- Show sample sizes; edge-profile findings are correlations in a small sample, not proof.
- Don't modify the user's CSV.
- Past performance analysis only, not financial advice.
