---
name: post-session-review
description: Post-session review of the user's opening-range setups. Use when the user asks how their opening-range (ORB) setups performed today, which symbols triggered their criteria, or what their hit rate was. Pulls the day's intraday bars, tests each symbol against the user's criteria, and reports triggers, outcomes, and hit rate.
---

# Post-Session Review (Opening-Range Setups)

Evaluate how the user's opening-range setups played out today: pull the day's bars, identify which symbols triggered the criteria, grade each outcome, and report the hit rate.

## Inputs

1. **Symbols:** from the user's message, or a watchlist/scan file in the working directory (e.g. `watchlist.*`, `symbols.*`). If neither exists, ask.
2. **Criteria:** the user's setup rules. Look in this order: the user's message, then a rules file in the working directory (e.g. `criteria.md`, `setup-rules.*`, `playbook.*`, `CLAUDE.md`). If none are found, ask the user to define them, or offer the defaults below and **state clearly that defaults were used**.
3. **Date:** today unless stated (use the last completed session if the market hasn't closed or it's a non-trading day).

### Default criteria (only if the user confirms or gives none)

| Item | Default |
|---|---|
| Opening range (OR) | first 15 minutes (9:30–9:45 ET): OR high/low |
| Long trigger | a 5-min candle closes above OR high |
| Short trigger | a 5-min candle closes below OR low |
| Entry | close of the trigger candle |
| Stop | opposite side of OR (or midpoint, if the user prefers) |
| Target / win | 1.5R reached before stop; otherwise graded at session close |
| Filters | OR range 0.5%–2% of price, volume confirmation (trigger bar volume above recent average) |
| Valid window | triggers before 11:30 ET |

## Process

1. **Pull data.** Get the day's intraday bars (1m or 5m) for each symbol from a finance MCP/browser tool or web source (TradingView, Yahoo, Barchart, etc.), plus prior close. State the source and interval. If bars can't be obtained for a symbol, list it as "no data" and exclude it from stats. Never estimate prices.
2. **Compute the OR** for each symbol: high, low, range, range % of price.
3. **Test the criteria** bar by bar: did a trigger occur, which direction, at what time, at what entry price? Record symbols that did **not** trigger, and which rule was missed (e.g. range too wide, no volume confirmation, no close beyond the range).
4. **Grade each trade** by walking forward from entry:
   - Which came first, stop or target? (Use the 1m bars when 5m bars are ambiguous within a bar, and flag any ambiguity.)
   - Outcome: **Win** (target hit first), **Loss** (stop hit first), **Open/Time-exit** (neither, marked at close with R achieved).
   - Compute R multiple, max favorable excursion (MFE) and max adverse excursion (MAE) in R.
5. **Stats:**
   - Triggers / symbols scanned
   - Hit rate = wins ÷ (wins + losses), and also hit rate counting time-exits as win/loss by sign of R (state both if time-exits exist)
   - Average R, total R, average winner vs. average loser, profit factor (if enough trades)
   - Long vs. short split, and morning vs. later trigger split
6. **Diagnose.** Identify patterns: did failed breakouts share a trait (low volume, wide OR, against the daily trend, chasing late, fading into prior-day levels)? Note any near-miss setups.

## Output format

Header: date, symbols scanned, criteria used (note if defaults), data source/interval.

**Trade table**

| Symbol | OR High/Low (range %) | Dir | Trigger time | Entry | Stop | Target | Outcome | R | MFE / MAE (R) |
|---|---|---|---|---|---|---|---|---|---|

**Not triggered:** a compact list with the reason for each.

**Scorecard:** triggers, wins, losses, time-exits, hit rate, avg R, total R, and a long vs. short split.

**Takeaways:** 2–4 bullets on what worked, what failed, and one concrete adjustment to test (e.g. "both losers triggered on below-average volume; require trigger-bar volume above 1.2x average").

## Rules

- Be honest about sample size: a handful of trades says little. Say so when n is small.
- Never fabricate bars, fills, or results. Mark unverifiable data "n/a" and leave it out of stats.
- Don't adjust the user's criteria after the fact to improve results; suggest changes only as a forward-looking test.
- Ignore slippage and commissions unless the user provides them, and note that results are theoretical fills at bar closes.
- If the user supplied actual trades or fills (journal/broker export), grade those instead and compare to the rule-based triggers.
- End with a one-line reminder that this is a review of past data, not financial advice.
