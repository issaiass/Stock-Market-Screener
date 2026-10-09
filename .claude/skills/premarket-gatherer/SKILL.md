---
name: premarket-gatherer
description: Stage 2.2 of the premarket analyst pipeline. Runs scan.py, a small keyless data gatherer (yfinance, feedparser, requests) that collects raw premarket data into packet.json with zero analysis. Use when the user wants to run, edit, or debug the gatherer, or needs the packet that feeds the analyst and merge prompts.
---

# Premarket Gatherer

`scan.py` (this folder) collects raw data into `packet.json`. It does no analysis: no conviction, no buckets, no opinions. The only computed judgment is the two deterministic eligibility flags that encode `watchlist-criteria/WATCHLIST_CRITERIA.md`.

## Run

```
.venv\Scripts\python .claude\skills\premarket-gatherer\scan.py [out.json]
```

Default output is `packet.json` in the current directory. It also keeps a `.econ_cache.json` (4-hour TTL) in the current directory because the calendar feed rate-limits.

## What goes in the packet

`generated_at`, `candidate_source` (`yfinance_screeners` or `static_universe`), `trading_day_note`, `scan_params`, `criteria`, `market_snapshot` (9 instruments), `econ_calendar` (USD High impact, today and tomorrow ET), `gappers` (top 12 by absolute gap, gap >= 4% and price >= $3), `market_news` (top 20 from 5 RSS feeds, SEO spam dropped), `gaps_to_fill`.

Each gapper has: ticker, name, price, prev_close, gap_pct (+ `gap_source`), market_cap, volume, `levels` (VWAP, HOD, LOD, premarket high and volume, open), `daily` (200-day SMA, prior high, prior close, 20-day avg volume), `rvol`, `next_earnings`, `headlines` (ranked, primary publishers first), `catalyst_found`, `day_eligible`, `swing_eligible`, `swing_catalyst_type`.

## Behavior worth knowing

- Gap and price use Yahoo's premarket fields when present, otherwise regular-market fields. `gap_source` says which. Before 9:30 ET, `open_is_proxy` is true and the premarket price stands in for the open.
- Headlines are kept only if they name the ticker on a word boundary or a distinctive company-name token. A stopword list (applied, advanced, technologies, etc.) stops generic words from matching alone. This is strict, so some real catalysts may be missed: `catalyst_found = false` means "nothing clean matched", not "no news".
- RVOL is full-day volume vs the 20-day average, because yfinance reports about 0 premarket volume. Real premarket RVOL needs a feed such as Alpaca, so `day_eligible` is a stand-in until then.
- Every network call is wrapped, so a bad ticker or feed never crashes the run. A failed calendar returns an empty calendar with a note or error.
- On weekends and before the daily bar prints, the "session" is the latest trading day found in the 5-minute bars.

## Tested

Ran against live Yahoo data outside premarket hours: snapshot, screeners, news, calendar, and enrichment all worked and produced a packet with 12 gappers. The calendar came back empty because there were no High-impact USD events that day. Not yet tested: the static-universe fallback path, a 429 from the calendar feed, and a true premarket run.

## Next stages

Feed `packet.json` to the analyst prompts, which fill `report-template/REPORT_TEMPLATE.md`. Keep this file small and judgment-free.

## Added to improve report quality

- **Plan math in code (`plan`):** for every gapper with intraday levels, the packet carries the Trend Join numbers so the AI judges instead of calculating: `trigger = max(premarket high, HOD)`, `stop = min(0.99 x premarket high, LOD)`, `r` (1R), `r_pct`, `target_1r`, `target_2r`, plus `position` (distance to VWAP, premarket high, HOD).
- **Per-ticker Google News RSS:** headlines are now also pulled from Google News per ticker (keyless), because yfinance per-ticker news often returns nothing. The strict ticker or distinctive-name filter still applies.
- **`analyst_changes`:** upgrades and downgrades from the last 3 days (firm, from, to, action, price target).
- **`options`:** nearest-expiry summary (call and put volume, open interest, call/put ratio, top call strike and whether its volume exceeds open interest). A simple summary, not true sweep or block data.
- **Premarket RVOL (optional):** yfinance reports 0 premarket volume, so a true premarket RVOL needs a feed. If `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY` are in `.env` (free Alpaca account, IEX feed), the packet gets `premarket_rvol` (today's premarket volume vs the average of the same window on prior sessions), and `day_eligible` uses it. Without keys it falls back to full-day RVOL and `rvol_basis` says so. The Alpaca path is untested until keys exist.
