---
name: catalyst-screener
description: Swing-trade catalyst screener for any sector. Use when the user asks for swing ideas, momentum movers, or catalyst plays in a {sector} (e.g. "top 10 liquid momentum movers in semiconductors with their latest catalyst and earnings date"). Returns a ranked table with catalyst, earnings date, and earnings-risk flags.
---

# Catalyst Screener

Given a `{sector}` (or industry/theme), return the top liquid momentum movers with their latest catalyst and next earnings date.

## Inputs (parse from the user's request; use defaults if unstated)

| Parameter | Default |
|---|---|
| sector | required — ask if missing |
| count | 10 |
| Price vs 200-day SMA (daily) | above |
| RVOL (relative volume) | > 1.5 |
| Market cap | > $2B |
| Earnings flag window | next 14 days |

User-stated filters override defaults. Add any extra filters they give (e.g. min price, avg volume).

## Process

1. **Build the universe.** Use WebSearch/WebFetch (or a finance MCP/browser tool if available) to find stocks in `{sector}` with market cap > $2B. Good sources: Finviz screener (`finviz.com/screener.ashx?v=111&f=cap_midover,sh_relvol_o1.5,ta_sma200_pa,sec_...` — adjust the sector/industry filter), Yahoo Finance screener, TradingView screener, Barchart. Prefer a screener URL with the filters preloaded over manual lookups.
2. **Apply filters.** Keep only names with: close above the 200-day SMA, RVOL > threshold, market cap > threshold. Also require adequate liquidity (avg daily volume ≳ 500K shares or ≳ $20M traded) so the names are tradeable.
3. **Rank by setup quality.** Score each name on:
   - Trend: distance above 200-day SMA (not overextended — >40% above is a caution), 50-day above 200-day, higher highs/lows
   - Momentum: 1-month/3-month relative strength vs sector and SPY
   - Volume: RVOL magnitude and whether volume confirms a breakout (close near high of day, breaking a base or prior resistance)
   - Catalyst quality: fresh, material, and not yet fully priced in
   - Risk/reward: proximity to a logical stop (e.g. 20/50-day MA, base low) vs. upside
   Take the top N.
4. **Find the catalyst.** For each name, search recent news (last ~5 trading days, widen to 30 days if nothing) for the driver: earnings beat/guide, upgrade, FDA/regulatory, contract/deal, M&A, product launch, sector/macro move. If none is found, write "No clear catalyst — technical/sector flow" rather than inventing one.
5. **Get the next earnings date.** Confirm from the company IR page, Yahoo, Nasdaq, or Finviz. Mark as "(est.)" if unconfirmed. Compute days until earnings from today's date.
6. **Flag earnings risk.** If earnings fall within the next 14 days, flag with ⚠️ and note that the setup carries gap risk (suggest sizing down, defining risk with options, or waiting for the print).

## Output format

Start with one line: sector, as-of date/time, filters applied, and data source.

Then a table sorted best setup first:

| # | Ticker | Company | Price | % vs 200D SMA | RVOL | Mkt Cap | Setup (quality 1–10) | Latest Catalyst (date) | Next Earnings | ⚠️ |
|---|---|---|---|---|---|---|---|---|---|---|

- Setup column: a short description (e.g. "breakout above 3-mo base on 2.1x vol") with the score.
- ⚠️ column: "⚠️ Earnings in N days" when within 14 days, else blank.

After the table, add:
- **Earnings-risk names:** list of flagged tickers.
- **Notes:** any names that narrowly missed filters, overextended names, or sector-level context (1–3 bullets).
- If fewer than N names pass the filters, return what passes and say so — never pad with names that fail the filters.

## Rules

- Data is time-sensitive: state the as-of time, and note if data is delayed or end-of-day.
- Never fabricate numbers, catalysts, or dates. If a value can't be verified, mark it "n/a" or "unverified".
- RVOL definitions vary by source; state which one was used.
- This is research, not financial advice — end with a one-line reminder to verify prices/levels and manage risk before trading.
