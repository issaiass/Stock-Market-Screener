# REPORT_TEMPLATE: Premarket Report (Claude Sonnet + Claude Haiku)

Blueprint for the analyst and merge prompts. Section order is fixed. Replace every `{{placeholder}}`. Voice and conventions are at the bottom.

---

# Premarket Report: {{Weekday, Month D, YYYY}}
*Claude Sonnet + Claude Haiku, independent passes. Written {{HH:MM}} ET.*

> Rules pick the watchlist, both AIs judge the quality. Not financial advice.

## Summary
- **The tape:** {{one line: futures, tone, the main driver}}
- **The catch we're watching:** {{one line: the single thing that could flip the day}}
- **Two-brain verdict:** {{one line: where Sonnet and Haiku agree or split, and the call}}

## Pre-Market Gappers
Every gapper gets its full catalyst headline, unshortened.

| Ticker | Gap % | Price | Premarket RVOL | Catalyst headline (full) |
|---|---|---|---|---|
| {{TICK}} | {{+X.X%}} | {{$X.XX}} | {{X.Xx}} | {{full headline, source, time}} |

## Day Trading Watchlist
Rule-picked: {{day trading filters, one line}}

| Ticker | Catalyst | Levels | Plan | Haiku check | Conviction |
|---|---|---|---|---|---|
| {{TICK}} | {{why it is moving}} | {{support / resistance / prior high}} | {{trigger, stop, first target}} | {{what Haiku agreed with or flagged}} | {{🟢 / 🟡 / 🔴}} |

## Swing Watchlist
Rule-picked: {{swing filters, one line}}

| Ticker | Catalyst | Trend context | Idea | Haiku check | Conviction |
|---|---|---|---|---|---|
| {{TICK}} | {{why it is moving}} | {{vs 50/200 SMA, base, extension}} | {{entry area, stop, hold plan}} | {{what Haiku agreed with or flagged}} | {{🟢 / 🟡 / 🔴}} |

**Conviction key:** 🟢 high, clean setup and catalyst, take it. 🟡 medium, good but needs a trigger or has a flaw. 🔴 low, watch only or skip unless something changes.

## Market Trends of the Day
- {{theme 1: sector or factor moving, with the number}}
- {{theme 2}}
- {{theme 3}}

## Technical Signals for Today
- **Index levels:** {{SPY / QQQ / IWM key levels}}
- **Breadth and volatility:** {{VIX, breadth, anything notable}}
- **Signals:** {{RSI extremes, divergences, breakouts, gap fills worth knowing}}

## Economic Data, Rates and the Fed
From the economic calendar. Times in ET.

| Time | Event | Forecast | Previous | Why it matters |
|---|---|---|---|---|
| {{HH:MM}} | {{event}} | {{fcst}} | {{prev}} | {{one line}} |

{{One line on rates, Fed speakers, or the rate-path read.}}

## Coming Up
- **Tomorrow's events:** {{data, speakers, auctions}}
- **Earnings:** {{tickers, before or after the bell, relevance to the watchlist}}

## Skips and Traps
- **{{TICK}}:** {{why to skip: no real catalyst, thin float, fading volume, gap into resistance, earnings gap risk}}

## Where the Two Brains Landed
- **Agreement:** {{names and calls both passes shared}}
- **Rules vs discretion:** {{names the filters picked that judgment downgraded, and names judgment likes that the filters missed}}
- **Sonnet's sharp catch:** {{one thing only Sonnet flagged}}
- **Haiku's sharp catch:** {{one thing only Haiku flagged}}

---

## Conventions

**Section order (fixed):** 1 Title and dated subtitle, 2 Disclaimer, 3 Summary, 4 Pre-Market Gappers, 5 Day Trading Watchlist, 6 Swing Watchlist, 7 Market Trends of the Day, 8 Technical Signals for Today, 9 Economic Data, Rates and the Fed, 10 Coming Up, 11 Skips and Traps, 12 Where the Two Brains Landed.

**Voice:** Casual and plain-spoken. Plain talk, first person, honest about uncertainty and what could go wrong. Short sentences. Admit when a setup is only okay. No hype, no guarantees.

**Hard rules:**
- No em dashes anywhere. Use commas, periods, colons or parentheses.
- Never invent numbers, headlines, levels or dates. Use "n/a" when unverified.
- Gappers keep the full catalyst headline.
- Every watchlist row gets a conviction color: 🟢 🟡 🔴.
- Haiku check column is filled from Haiku's independent pass, not guessed.
- Keep the disclaimer to one line.
