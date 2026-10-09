---
name: pnl-audit
description: Basic P&L audit of a broker trade export (CSV). Use when the user provides a broker CSV and asks to analyze real trading performance - realized P&L, win rate, avg win/loss, best/worst trades, stocks and days, and a split by holding period. Reconciles to the broker's own realized P&L before showing results.
---

# P&L Audit

Analyze the user's broker CSV export. Do the calculation in code (Python/pandas via Bash or PowerShell), not by eye. Order matters: **validate and reconcile first, then analyze.**

## Inputs

- Path to the CSV (from the message, or look in the working directory for `*.csv`). Ask if ambiguous.
- Optional: a broker realized-P&L summary file or figure for reconciliation. Many brokers include it in the export (a "Realized P&L" report/section) or on a separate statement. If none is provided, ask for it, and say reconciliation was not possible if it is unavailable.

## Step 1: File check (report before anything else)

- Confirm the file opens; show the detected columns and how each was mapped (date/time, symbol, side/action, quantity, price, fees/commission, amount, any realized P&L column).
- Handle common export quirks: header/footer or summary rows, multiple sections, currency symbols, thousands separators, parentheses for negatives, mixed date formats, options contract multipliers (x100), and non-trade rows (dividends, transfers, interest, fees). Exclude non-trade rows and say how many.
- Report: **date range** (first to last trade date) and **number of order rows** (and number of fills/executions if different). Note rows that were dropped or unparsable.
- If a needed column is missing or ambiguous (e.g. side), stop and ask rather than guessing.

## Step 2: Reconcile with the broker (gate)

- Compute total realized P&L from the data (state fee treatment: net of fees if the broker's figure is net).
- Compare with the broker's realized P&L summary. Show both numbers and the difference.
- If they match (within rounding, ~$1): proceed.
- If they don't: **do not present the analysis as final.** Investigate likely causes (fees/commissions, wash-sale adjustments, positions opened in prior years so sells have no buys in file, corporate actions/splits, options expiry/assignment, short sales, FIFO vs. average-cost method differences) and report the gap and cause. Try the broker's lot method (FIFO unless stated). Only continue once the gap is explained, or show results clearly labeled "UNRECONCILED" with the discrepancy.

## Step 3: Rebuild completed round trips

- Group by symbol (for options, by full contract). Process fills chronologically (use timestamp, then file order).
- Track the running position per symbol. A **trade** starts when the position goes from flat to non-zero and ends when it returns to flat. Scaling in/out across many fills is **one trade**.
- Long and short trades both count. If a fill crosses through zero (e.g. long 100, sell 150), split it: close the long, open a short with the remainder.
- P&L per trade: use FIFO lot matching of fills (or the broker's stated method) so it reconciles; sum realized P&L across the trade, net of fees where available.
- Record per trade: symbol, direction, open datetime, close datetime, number of fills, max size, avg entry, avg exit, net P&L, holding days.
- **Open positions** (non-flat at the end of the file) are excluded from all stats. List them separately with symbol and quantity, so the user knows they were ignored.
- Sells with no matching buy in the file (position opened before the export) cannot form a complete trade: exclude, list them, and note the effect on reconciliation.

## Step 4: Metrics to present

1. **Summary:** total realized P&L, number of completed trades, win rate (wins / trades; breakeven trades counted separately), average win vs. average loss, win/loss ratio, profit factor, and expectancy per trade.
2. **Biggest winner and biggest loser:** symbol, open and close dates, P&L, and the number of fills each took.
3. **Best and worst stocks** by total P&L (top and bottom 5, with trade count and win rate).
4. **Best and worst single days** by realized P&L (day = close date of the trade). Top and bottom 5.
5. **Holding-period buckets:** same-day (opened and closed on the same calendar date), next-day/overnight (closed on the next calendar day), multi-day (everything longer). For each: number of trades, total P&L, win rate, avg P&L. Buckets must sum to the totals. Say which calendar and time zone were used.

## Output format

1. File check (date range, order rows, columns, exclusions)
2. Reconciliation table: computed vs. broker, difference, status ✅/⚠️
3. Metrics, in compact tables
4. Exclusions: open positions, unmatched sells, ignored rows
5. 2–4 plain observations from the data (e.g. losers bigger than winners, one bucket carrying the P&L, concentration in a few trades). No advice beyond what the data shows.

## Rules

- Never present figures that weren't computed from the file. Never fill gaps with guesses.
- Show the code approach briefly or save the script (e.g. `pnl_audit.py` in the working directory) so the user can rerun it.
- Mention sample size when the number of trades is small.
- Don't change or overwrite the user's CSV.
- End with a one-line note that this is analysis of past data, not financial or tax advice.
