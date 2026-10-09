---
name: strategy-deep-dive
description: Trading-journal-style deep dive on completed trades from a broker CSV. Use after (or together with) the pnl-audit skill when the user wants strategy-level stats by long/short, holding period, entry weekday and entry time, a performance calendar with streaks and max drawdown, overtrading and discipline checks, a "hidden leaks" list, and a profile of what winning vs losing stocks have in common with screening advice.
---

# Strategy Deep Dive

Go deeper on the user's completed trades. Compute everything in code (pandas), not by eye.

## Prerequisite: trades must be rebuilt and reconciled

Use the same completed round trips as the `pnl-audit` skill: reuse its saved `pnl_audit.py` / trades table if one exists in the working directory. Otherwise follow that skill's Steps 1-3 first (file check, reconcile to the broker's realized P&L, rebuild round trips with scaled fills as ONE trade, exclude open positions). Do not present results that failed reconciliation without labeling them **UNRECONCILED**.

Each trade needs: symbol, direction, entry datetime, exit datetime, fills, max/avg position size (shares and dollars), avg entry/exit, net P&L, holding time.

## Standard stat block (use for every cut)

Trades, total P&L, win rate, avg win, avg loss, profit factor (gross wins / gross losses), and **expectancy per trade** (avg P&L, equivalently WR x avg win - LR x avg loss). Add a **low-sample flag** to any bucket with fewer than 20 trades (and say "anecdotal" under 10). Never draw conclusions from tiny buckets without that caveat.

## 1. Strategy-level cuts

Show one table per cut using the standard block:
- Long vs short
- Holding period: same-day / overnight (closed next calendar day) / multi-day
- Weekday of **entry** (Mon-Fri)
- Time of day of **entry**, in ET: 9:30-10:00, 10:00-11:00, 11:00-14:00, after 14:00 (state the time zone conversion applied; flag pre-market entries and put them in a separate "pre-market" bucket)

Buckets in each cut must sum to the overall totals.

## 2. Performance calendar

- Daily realized P&L (day = trade close date) as a calendar grid or heatmap, green/red days, green-day %, avg green day vs avg red day
- Longest green streak and longest red streak (days), with start/end dates and P&L of each
- Cumulative P&L curve and **max drawdown** ($ and % of peak equity if a starting balance is known, otherwise in $), with the peak date, trough date, and recovery date (or "not recovered")
- If charting, load the `dataviz` skill first; otherwise a text table is fine

## 3. Overtrading check

Group trading days by the number of distinct tickers traded that day: 1-2, 3, 4+. For each group: number of days, total and avg daily P&L, win rate per trade, expectancy per trade, avg loss. Answer directly: is the user worse when juggling more names? Mention sample size and whether trade count per day (not just ticker count) tells a different story.

## 4. Discipline check

- Winners vs losers: average position size (shares and $), average hold time (and median), average fills per trade
- Share of total profit from the **top 5 trades**; also of gross wins; and P&L excluding the top 5 (is the edge dependent on a few outliers?)
- Longest losing streak (in trades) with dates and total loss
- Whether losers are held longer than winners, or sized larger (classic leak: cutting winners, holding losers)

## 5. Hidden leaks

Search the cuts above (and combinations such as short x after 2pm, Friday x overnight, 4+ tickers x large size) for conditions with consistent losses. Report **3-5 leaks**, each with: the exact condition, number of trades, total $ lost, win rate, expectancy, and the sample caveat. Prefer conditions that persist across months (not one bad week). Rank by dollars lost. Don't data-dredge: say how many combinations were tested and treat the findings as hypotheses.

## 6. What winners and losers have in common

Take the top ~10-20 winning and top ~10-20 losing trades and stocks (by $). Enrich each with market data from a free source (yfinance via Python, or web sources) **as of the entry date**:
- Technicals: price vs 20/50/200 SMA, RSI(14), ATR% / ADR% (20-day), gap % at entry, distance from 52-week high, trend direction
- Volume/liquidity: relative volume on entry day, avg dollar volume
- Float and market cap, share price, short interest if available
- Sector/industry
- News: earnings on or near the entry date, other catalysts
- Volatility and the day's range

Compare the two groups feature by feature (medians, and the % of each group meeting a condition). Only report differences that are meaningful given the sample size, and state that these are correlations in a small sample, not proof. Note missing data (delisted tickers, unavailable float history) and how it was handled.

Then give, in plain language:
- **Focus on:** the kinds of stocks where the user's winners cluster (with the concrete ranges, e.g. price $15-40, ADR 4-8%, RVOL > 2, catalyst present)
- **How to screen for them:** specific filters usable in Finviz/TradingView (or the `catalyst-screener` / `premarket-report` skills' `config.json`)
- **Avoid:** the profile of the losers, with the same concrete ranges

## Output format

1. One-paragraph executive summary (reconciled total P&L, trade count, the single biggest finding)
2. Sections 1-6, each with compact tables and a 1-2 line takeaway
3. **Top-3 action items** that follow directly from the data (e.g. "stop trading after 2pm: -$X over N trades")

## Rules

- Never fabricate numbers; mark missing data "n/a" and exclude it from stats.
- Always show sample size; flag fragile buckets.
- Don't change the user's CSV. Save the analysis script (e.g. `strategy_deep_dive.py`) so it can be rerun.
- This is analysis of past data, not financial advice; past patterns may not persist.
