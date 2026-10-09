---
name: watchlist-criteria
description: Stage 2.1 of the premarket analyst pipeline. Holds WATCHLIST_CRITERIA.md, the source-of-truth spec for the user's two validated setups (Day Trading "Trend Join Long" and the Swing watchlist) with backtest stats. Use when writing, checking, or changing the scanner rules, or when an analyst prompt needs the exact selection criteria and intraday plan.
---

# Watchlist Criteria

`WATCHLIST_CRITERIA.md` (in this folder) is the source of truth for the two validated setups. The scanner encodes it; if they disagree, the file wins.

## Summary

**Day Trading, "Trend Join Long"** (54.6% win rate, PF 1.59, 280 trades). All required: gap > 3%, price > $3, market cap > $1B, premarket RVOL > 1.5, price breaking above yesterday's high. Plan: 10:00am to 3:30pm ET window; trigger > premarket high AND > prior high-of-day; stop 1% below premarket high or LOD (lower of the two) = 1R; scale 1/3 at +1R, 1/3 at +2R, trail the last 1/3 on the 21-EMA; flat by 3:51pm.

**Swing** (57.6% / PF 5.34 on news catalysts; 44.7% / PF 2.57 on earnings catalysts). All required: gap >= 8%, price > $3, open > yesterday's high, open > 200-day SMA, market cap >= $800M, a real catalyst (earnings on the gap day, or news with no earnings). Entry and exit management is still being built, so swing entries are starter ideas only. Never add stops or targets.

## How to use it

- **Scanner:** make `premarket-report/scripts/config.json` and `check_day` / `check_swing` match the file exactly. Note the strict vs inclusive signs (`>` vs `>=`). If a rule changes, edit `WATCHLIST_CRITERIA.md` first, then the config.
- **Analyst prompts:** quote the criteria from the file, do not paraphrase. Day-trading rows may show levels and the plan from the intraday rules; swing rows show catalyst type and a starter idea only.
- **Validation:** when asked to check the scanner against the spec, compare each threshold and sign, and list mismatches.
- **Known gap to fix when the scanner is next touched:** the day-trading intraday plan (trigger, stop, scaling, 21-EMA trail) is not in the script, which only does premarket selection. The swing catalyst should also be tagged earnings vs news in the report.

## Style

Casual, plain-spoken voice, no em dashes anywhere (search for the character before delivering). Backtests are past results, not promises, and this is not financial advice.

## Implementation notes

- The Trend Join stop, 1R and the +1R/+2R targets are computed in code (`plan` in the packet), not by the model: `trigger = max(premarket high, HOD)`, `stop = min(0.99 x premarket high, LOD)`.
- Day RVOL uses true premarket RVOL when Alpaca keys are configured, otherwise full-day RVOL from Yahoo (`rvol_basis` in the packet says which).
