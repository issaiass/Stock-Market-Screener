---
name: premarket-report
description: Automated premarket report for the 8:45am ET read. Runs a Python script (free Yahoo Finance + economic calendar data) that lists premarket gappers matching Day Trading and Swing watchlist filters, today's economic events, analyst rating changes, and options flow. Use to run, edit the filters of, or schedule the daily report.
---

# Premarket Report

A schedulable Python script that builds a clean text report: economic events, qualifying tickers (ticker, gap %, price, catalyst headline, which watchlist), top gappers for context, analyst upgrades/downgrades, and options flow.

Files (in this skill folder):
- `scripts/premarket_report.py` the report
- `scripts/config.json` all filters (edit this, not the code)
- reports are written to `scripts/reports/premarket_YYYY-MM-DD.txt`

## Filters (defaults in config.json)

**Day trading** (all required): gap > 3% vs prior close; price > $3; market cap > $1B; premarket RVOL > 1.5; price above yesterday's high.

**Swing** (all required): gap >= 8%; price > $3; price above yesterday's high and above the 200-day SMA; market cap >= $800M; a real catalyst (earnings today, or a news headline in the last 18h).

### Changing the filters

When the user gives different filters, edit `scripts/config.json`, not the script:
- `watchlists.day_trading.*` / `watchlists.swing.*` thresholds (`min_gap_pct`, `min_price`, `min_market_cap`, `min_premarket_rvol`)
- toggles: `require_above_prior_high`, `require_above_sma200`, `require_catalyst`
- `universe.min_market_cap` must be <= the lowest watchlist market-cap filter, and `universe.min_price` <= the lowest price filter
- `report.news_lookback_hours`, `report.econ_impacts`, `report.options_flow_top_n`

If the user wants a filter that has no key (e.g. a max float or sector), add it to `config.json` and to `check_day` / `check_swing` in the script.

## Run

```
pip install yfinance pandas requests
python .claude/skills/premarket-report/scripts/premarket_report.py
```

Takes a few minutes (it scans ~3,000 US names, then enriches only the gappers). Progress goes to stderr, the report to stdout and the report file.

## Schedule (Windows Task Scheduler)

Run at 8:35 ET so it is ready at 8:45 ET. Task Scheduler uses the PC's local time zone; convert 8:35 ET to local time (and recheck after DST changes).

```
schtasks /Create /TN "PremarketReport" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:35 ^
  /TR "python C:\Users\Denys\Downloads\trading-tools\.claude\skills\premarket-report\scripts\premarket_report.py"
```

(If the PC is set to Eastern time, `/ST 08:35` is correct as written.) The PC must be on and awake. Use the full path to `python.exe` if the task can't find it.

## Data caveats (state these if the user asks about accuracy)

- Yahoo data is free and may be delayed or incomplete; premarket volume is thin.
- "Open above yesterday's high" is evaluated using the premarket price, since the market has not opened yet.
- Premarket RVOL is premarket volume so far vs the average of the same 4:00-to-now window over the previous ~5 sessions (Yahoo only serves ~7 days of 1m data).
- The economic calendar is the free Forex Factory weekly feed (US events, medium/high impact).
- Analyst changes and options flow are only checked for the gappers in the report, since Yahoo has no market-wide free feed.
- Options flow is a simple summary of the nearest expiry (call/put volume, open interest, a hot-call flag), not true sweep or block data.
- The screener only finds US stocks (NASDAQ, NYSE, AMEX) above the universe floors.

## Verification status

Tested outside market hours: the universe scan, economic calendar, and batch price fallback work. The full gapper path (filters, RVOL, catalyst, options) has not been exercised against live premarket data. On the first live morning, check the output against a premarket scanner and fix any field mismatches.

Research only, not financial advice.
