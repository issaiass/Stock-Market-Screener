---
name: multi-timeframe-check
description: Multi-timeframe alignment check for a single ticker. Use when the user asks to check trend alignment across 1m/5m (day trend) and daily/weekly (swing trend), flag RSI divergences, and say whether price is in premium or discount vs the daily range. Example - "For NVDA, check alignment across 1m/5m for the day trend and daily/weekly for the swing trend."
---

# Multi-Timeframe Check

For a given `{ticker}`, assess trend alignment on intraday (1m/5m) and swing (daily/weekly) timeframes, flag RSI divergences, and locate price within the daily range (premium vs discount).

## Inputs

- **ticker:** required. Ask if missing.
- Optional overrides from the user: different timeframes, RSI length (default 14), or trend method.

## Data

Get OHLCV and indicators from whatever is available: a finance MCP/browser tool, or web sources (TradingView, Yahoo Finance, Finviz, Barchart, StockCharts). State the as-of time and whether data is live, delayed, or end-of-day. If intraday (1m/5m) data is unavailable or the market is closed, use the last session's intraday data and label it as such. Never guess values you couldn't read.

## Process

### 1. Trend per timeframe (1m, 5m, daily, weekly)
Classify each as **Bullish / Bearish / Neutral (range)** using these factors:
- Market structure: higher highs/higher lows (bull) vs lower highs/lower lows (bear)
- Price vs key moving averages: 1m/5m — 9/20 EMA and VWAP; daily — 20/50/200 SMA; weekly — 10/40 week (≈50/200 day) SMA
- MA stack order and slope
- Most recent break of structure

Record a one-line justification and the nearest support/resistance for each.

### 2. Alignment
- **Day trend:** do 1m and 5m agree? (Aligned bullish / aligned bearish / conflicted)
- **Swing trend:** do daily and weekly agree?
- **Overall:** are day and swing aligned? Classify as **Full alignment**, **Partial** (e.g. swing bullish, day pulling back), or **Conflict**. Say what a pullback-in-trend vs counter-trend trade would look like.

### 3. RSI divergences
On each timeframe, compare the last two swing highs/lows in price against RSI(14):
- **Regular bearish:** price higher high, RSI lower high (reversal warning)
- **Regular bullish:** price lower low, RSI higher low
- **Hidden bullish:** price higher low, RSI lower low (trend continuation)
- **Hidden bearish:** price lower high, RSI higher high
Report type, timeframe, and the swing points involved (approx. price/RSI values and dates/times). Also note overbought (>70) / oversold (<30). If none, write "No divergence". Mark a divergence as unconfirmed until price breaks structure.

### 4. Premium / Discount vs the daily range
- Define the range: today's session high and low (and, as context, the prior day's range or the 20-day range if useful). State which was used.
- Equilibrium = midpoint of the range. Position % = (price − low) / (high − low).
- **Premium** if above 50% (stronger above ~70%), **Discount** if below 50% (stronger below ~30%), **Equilibrium** near 50%.
- Give the levels: range high, 50% level, range low, and the current price.
- Interpret relative to trend: in an uptrend, discount is the preferred long area; in a downtrend, premium is the preferred short area.

## Output format

Header: ticker, price, as-of time, data source.

**Trend table**

| Timeframe | Trend | Basis | Key level | RSI(14) | Divergence |
|---|---|---|---|---|---|
| Weekly | | | | | |
| Daily | | | | | |
| 5m | | | | | |
| 1m | | | | | |

**Alignment:** Day trend (1m/5m): …, Swing trend (daily/weekly): …, Overall: Full / Partial / Conflict.

**Premium/Discount:** range high / 50% / low, price, position %, verdict.

**Bottom line:** 2–4 sentences: bias (long / short / wait), what ideal entry zone looks like (e.g. pullback to discount near 5m VWAP in aligned uptrend), invalidation level, and the biggest conflict or risk (e.g. bearish daily divergence, earnings date).

## Rules

- Flag upcoming earnings or major events within 2 weeks with ⚠️.
- Never fabricate prices, RSI values, or levels. Mark unverifiable values "n/a".
- Keep it concise and scannable.
- End with a one-line reminder that this is research, not financial advice; verify levels before trading.
