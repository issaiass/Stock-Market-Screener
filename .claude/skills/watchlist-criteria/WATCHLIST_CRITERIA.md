# WATCHLIST_CRITERIA: The Two Validated Setups

These are my rules. They are the source of truth, and the scanner encodes them exactly as written. If the scanner and this file disagree, this file wins.

Backtest numbers are from my own testing. Past results, small samples, not financial advice.

---

## 1. Day Trading Watchlist: "Trend Join Long"

**Backtest:** 54.6% win rate, profit factor 1.59, 280 trades.

Honest take: a 54.6% win rate with a 1.59 profit factor is a solid, boring edge. It works because the winners get paid and the losers get cut at 1R, not because I'm right a lot.

### Premarket selection (all required)

| Rule | Threshold |
|---|---|
| Gap % vs previous close | > 3% |
| Price | > $3 |
| Market cap | > $1B |
| Premarket relative volume (RVOL) | > 1.5 |
| Price vs yesterday's high | Breaking above it |

Miss any one and it is off the list. No "close enough".

### Intraday plan

| Item | Rule |
|---|---|
| Trading window | 10:00am to 3:30pm ET |
| Trigger | Price > premarket high AND price > prior high-of-day |
| Stop | 1% below the premarket high, or the low of day (LOD), whichever is lower. This distance = 1R |
| Scale out | 1/3 at +1R, 1/3 at +2R |
| Runner | Trail the last 1/3 on the 21-EMA |
| Flat by | 3:51pm ET |

Notes:
- The stop sets the size of 1R. Size the position off it before entering, not after.
- No entries before 10:00am. The open is noise and I do not need to trade it.
- Nothing carries overnight. Flat by 3:51pm, no exceptions.

---

## 2. Swing Watchlist

**Backtest:**
- News catalysts: 57.6% win rate, profit factor 5.34
- Earnings catalysts: 44.7% win rate, profit factor 2.57

Honest take: news catalysts tested better than earnings catalysts, and the earnings win rate is under 50% (the profit factor still carries it because the winners are big). Do not read the 5.34 as a promise. Check the sample size before trusting it.

### Premarket selection (all required)

| Rule | Threshold |
|---|---|
| Gap % vs previous close | >= 8% |
| Price | > $3 |
| Open vs yesterday's high | Open > yesterday's high |
| Open vs 200-day SMA | Open > 200-day SMA |
| Market cap | >= $800M |
| Catalyst | A real one: earnings on the gap day, OR news with no earnings |

Tag every swing name with its catalyst type (earnings or news), because the two behave differently in the backtest.

### Entry and exit management

Still being built. Swing entries are **starter ideas only**: no stops, no targets, no sizing rules for now. Anything that shows a stop or target here is made up, so do not add one.

---

## Scanner notes

- Day trading and swing use different cutoffs on purpose (gap > 3% vs >= 8%, market cap > $1B vs >= $800M). Mind the strict vs inclusive signs.
- Premarket price stands in for "the open" until the bell. Flag swing names to re-check at the open.
- A name can hit both lists. Show both tags.
- If data for a rule is missing (RVOL, SMA, catalyst), the name does not qualify. Mark it "n/a", never guess.

## Changing a rule

Edit this file first, then the scanner config (`premarket-report/scripts/config.json`). If you backtest a change, put the new numbers in this file too.
