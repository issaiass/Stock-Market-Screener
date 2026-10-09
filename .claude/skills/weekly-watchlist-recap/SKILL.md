---
name: weekly-watchlist-recap
description: Weekly recap of the user's watchlist. Use when the user asks to summarize last week's performance and catalysts for their watchlist, or for a weekend/Monday-prep review. Per name gives weekly % move, RVOL, dated catalyst, key technical level, one risk, and ends with the top 3 setups for next week.
---

# Weekly Watchlist Recap

Summarize last week's performance and catalysts for the user's watchlist, then pick the top 3 setups going into next week.

## Inputs

- **Watchlist:** take tickers from the user's message. If none are given, look for a watchlist file in the working directory (e.g. `watchlist.txt`, `watchlist.csv`, `watchlist.md`). If neither exists, ask the user for the tickers before proceeding.
- **Week:** the last completed trading week (Monday–Friday, adjusting for holidays). State the exact date range used, based on today's date.

## Process

1. **Prices and weekly move.** For each ticker, get the prior Friday close and last Friday close; compute weekly % change. Also note the move vs SPY (and the sector ETF if obvious) for relative strength.
2. **RVOL.** Use weekly-average volume vs. the 50-day (or 3-month) average daily volume, and note the peak single-day RVOL of the week. State which definition was used.
3. **Catalyst.** Search news for the week for each name. Name the specific catalyst and its date (earnings, guidance, upgrade/downgrade, FDA/regulatory, contract, M&A, macro/sector move, insider/13F activity). If no company-specific catalyst, write "No clear catalyst — sector/market flow" and name the sector driver if known. Never invent a catalyst.
4. **Key technical level.** Give one level to watch with its type and distance from the current price: e.g. 50-day SMA, 200-day SMA, prior high/low, breakout/base level, gap fill, VWAP from earnings. Say whether it is support or resistance.
5. **One risk.** One specific, concrete risk (e.g. earnings on a given date, loss of the 50-day, overextension, dilution, macro event like CPI/FOMC, customer concentration). Include upcoming earnings dates within the next two weeks here.
6. **Rank next-week setups.** Score on trend, relative strength, volume confirmation, catalyst freshness, and risk/reward to a defined level. Pick the top 3.

## Output format

Header: date range covered, number of tickers, data source and as-of time.

**Table** (sorted by weekly % move, best to worst, unless the user prefers otherwise):

| Ticker | Weekly % | vs SPY | RVOL (avg / peak) | Catalyst (date) | Key level to watch | Risk |
|---|---|---|---|---|---|---|

**Week in brief:** 2–4 bullets on watchlist-wide themes (leaders/laggards, sector rotation, macro drivers).

**Top 3 setups for next week:** for each, give
- Ticker and thesis (1–2 sentences)
- Trigger / entry area, invalidation level (stop), and the first target
- Key event risk next week (earnings, data releases)

## Rules

- Never fabricate prices, volumes, dates, or catalysts. Mark unverifiable values "n/a".
- Keep each cell concise; the table should be scannable.
- Flag any name reporting earnings next week with ⚠️.
- If the watchlist is large (>25 names), still cover every name, but keep per-name text to one line.
- End with a one-line reminder that this is research, not financial advice, and levels should be verified before trading.
