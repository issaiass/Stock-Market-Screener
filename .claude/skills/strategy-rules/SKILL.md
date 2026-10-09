---
name: strategy-rules
description: Test the user's written trading rules against their audited trades and market data, then produce a revised one-page rulebook where every change traces to a number. Use when the user pastes strategy rules (setup, entry, exits) and asks to optimize or validate them against the evidence in their trade history.
---

# Strategy Rules

Evidence-check the user's written rules against their own audited trades, then output a revised rulebook. Compute everything in code (pandas); do not argue from intuition.

## Inputs

- **Rules:** from the user's message, or a rules file in the working directory (`rules.md`, `playbook.*`). Keep a verbatim copy.
- **Audited trades:** completed round trips from the `pnl-audit` skill (file check, reconciled to broker realized P&L, scaled fills = one trade, open positions excluded). Reuse a saved trades table/script if present; otherwise run that skill's steps first. If reconciliation fails, label every result **UNRECONCILED**.
- **Market data:** the `pnl-dashboard` skill's enrichment (configured market data API if present, else `yfinance`; reuse its cache). Features are measured **as of the entry date with no look-ahead** (use data through the prior close unless the rule is about the entry day itself).

### Baseline rules (the user's current swing rulebook; use if none newer is given)

- **Setup:** market leader breaking out to new highs, within 25% of 52-week high; above 200-day SMA; ADR 4-8%; liquid ($50M+ traded per day)
- **Entry:** the breakout over the recent high
- **Exits:** wide stop, hold for weeks, let the runner work

## Step 1: Make each rule testable

Translate every rule into a measurable condition and state it before testing, e.g.:
- within 25% of 52-week high: (52w high - entry price) / 52w high <= 25%
- above 200-day SMA: entry price > SMA200
- ADR 4-8%: 20-day average of (high/low - 1), in %
- liquid: 20-day average (close x volume) >= $50M
- market leader: relative strength proxy (e.g. 3- and 6-month return rank vs SPY, or in top quartile of the user's traded names); state the proxy used
- breakout entry: entry price at/above the highest high of the prior N days (state N, e.g. 20); mark non-breakout entries (pullback/gap-and-go)
- wide stop / hold for weeks: realized hold time and loss size vs ADR (e.g. loss in ADR multiples), % of trades held >= 10 trading days

If a rule cannot be measured with the data, say so and do not pretend to test it.

## Step 2: Test each rule against the trades

For each rule, split trades into **meets** vs **violates** and give the standard stat block: n, total P&L, win rate, avg win, avg loss, profit factor, expectancy per trade. Verdict per rule:
- **Supported:** meeting trades clearly better (expectancy and profit factor), with enough sample
- **Contradicted:** violating trades equal or better, or the rule's bucket loses
- **Inconclusive:** too few trades (< 20 per side = low-sample flag; < 10 = anecdotal) or a tiny difference

Report the effect with a sample-size-aware check (e.g. bootstrap CI on the expectancy difference, or at least a permutation/ t-test p-value) and avoid over-reading it. Also break out the dose-response: expectancy by bin of each continuous measure (ADR in 2% steps, distance from high in 10% steps, etc.), so thresholds come from the data, not guesses.

## Step 3: Exit question (intraday vs overnight)

Settle with data which holding choice made money. Report:
- Realized results by holding period: **same-day** (closed intraday), **overnight/next-day**, **multi-day / weeks**: n, P&L, win rate, PF, expectancy
- The **overnight effect**: for trades held across the close, split P&L into close-to-open (overnight gap) vs open-to-close (intraday) components using daily bars, summed over the holding days. Show which component made or lost the money
- Counterfactuals (clearly labeled hypothetical, using entry/exit dates and daily bars): exit at the close of entry day; exit at day 1/3/5/10/20 close; the user's actual exit; max-favorable excursion vs actual exit (how much of the move was given back); and loss size vs ADR (is the "wide stop" actually tolerable?)
- If the user's rule says "hold for weeks": check whether trades held >= 10 days outperform shorter ones, and whether the runners carry the P&L (share of profit from top 5 trades, P&L without them)

State assumptions (fills at close prices, no slippage). Answer the question directly in one sentence with the numbers.

## Step 4: Market-data checks at entry dates

For each rule's measures plus the extras below, report outcome by bin (expectancy, win rate, n):
- Gap size at entry (%)
- ADR (%)
- Extension from the 8-EMA ((price / EMA8 - 1) in % and in ATR multiples)
- Market regime that day: SPY vs 200-day SMA, SPY vs 20-day, VIX bucket (<15, 15-20, 20-30, >30)
- Optionally: RVOL, RSI(14), earnings within a window, sector, float, price

## Step 5: Verdict lists

- **KEEP as-is:** rule, the numbers that support it
- **TIGHTEN or LOOSEN:** rule, current threshold, proposed threshold, and the number that justifies it (e.g. "ADR 4-8% -> 3-6%: trades with ADR 6-8% lost $X over N trades, expectancy -$Y")
- **MISSING:** new rules the data suggests (e.g. "skip entries > 1.5 ATR above the 8-EMA: N trades, -$X", "no new longs when SPY < 200-day SMA"), each with its evidence
- **Can't be tested / needs more data:** say so honestly

Guard against overfitting: prefer round thresholds, require the effect to hold in both halves of the date range (split-sample check), report how many thresholds were tried, and drop changes whose evidence is low-sample. Tag each change with confidence (high / medium / low).

## Step 6: Output the revised rulebook (one page)

A single page (about 40 lines) containing: Setup, Entry, Exit/Risk, Market-regime filter, Do-not-trade list. **Every changed or added line carries a trace tag** pointing to the number, e.g. `[ADR <= 6%: ADR 6-8% bucket = -$4,210 over 17 trades, PF 0.6; low-sample]`. Unchanged rules are marked `[kept: PF 1.8, n=42]`. Add a short "evidence table" below listing each change, old vs new, the supporting numbers, n, and confidence.

Save as `revised_rulebook.md` in the working directory and show it in the reply. Save the analysis script (`strategy_rules.py`) so it can be rerun as more trades arrive.

## Rules

- Never fabricate numbers; mark missing data "n/a" and exclude it from stats.
- Every change must trace to a computed number; if no number supports a change, don't make it.
- Don't rewrite the user's rules to flatter results; show where their data contradicts them plainly.
- Show sample sizes everywhere. Small-sample findings are hypotheses, not facts, and past patterns may not persist.
- Don't modify the user's CSV. Analysis of past data, not financial advice.
