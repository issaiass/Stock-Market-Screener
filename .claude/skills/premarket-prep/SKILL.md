---
name: premarket-prep
description: Premarket prep scanner. Use when the user asks for this morning's top momentum movers, premarket movers, or a pre-open game plan, e.g. "top 10 momentum movers this morning with volume over 2x baseline and an opening range between 0.5-2%, ranked by setup quality". Returns a ranked table with catalysts, key levels, and trade plans.
---

# Premarket Prep

Find the best momentum setups heading into the open, filtered by volume and range, ranked by setup quality.

## Inputs (parse from the request; defaults if unstated)

| Parameter | Default |
|---|---|
| count | 10 |
| Volume vs baseline | > 2x |
| Opening range | 0.5%–2% |
| Min price | $5 |
| Min avg daily volume | 500K shares |
| Min market cap | $1B (state if relaxed) |
| Sector / universe | all US stocks (or the user's watchlist/sector) |

User filters override defaults.

## Definitions (state them in the output)

- **Volume vs baseline:** premarket volume so far divided by the average premarket volume at the same time of day over the last ~20 sessions. If that isn't available, use premarket volume as a % of average daily volume and say so. Report as a multiple (e.g. 3.2x).
- **Opening range:** premarket range = (premarket high − premarket low) / previous close, in %. If the user is running this after the open, use the first 5/15/30-minute range instead, and state which. Also report the gap % vs prior close.

## Process

1. **Check timing.** Note the current time (ET) and the market session. If the market is closed and it isn't premarket, say so and label results as of the last session.
2. **Build the candidate list.** Use WebSearch/WebFetch (or a finance MCP/browser tool if available) for premarket gainers/movers (Finviz, Yahoo, TradingView, Benzinga, Barchart premarket pages). Include both upside and downside momentum unless the user wants long-only.
3. **Apply filters.** Keep names meeting the volume multiple, range band, and liquidity/price requirements. Drop illiquid or sub-threshold names, OTC, and tickers with ultra-wide spreads.
4. **Find the catalyst.** Search news for each name (last 24 hours): earnings, guidance, upgrade/downgrade, FDA/regulatory, deal/M&A, contract, macro or sector read-through. If none is found, write "No clear catalyst" rather than guessing.
5. **Technical context.** Identify the key levels: previous close, premarket high/low, prior-day high/low, 50/200-day SMA, nearby resistance or support.
6. **Rank by setup quality.** Score 1–10 on:
   - Catalyst quality (fresh, material, durable vs. one-off)
   - Volume strength (multiple of baseline, sustained vs. a single spike)
   - Clean technical structure (breaking resistance/base, trend alignment, room to run)
   - Range quality (orderly, within the band, not chaotic)
   - Risk/reward to a clear stop level
   - Liquidity/spread
   Take the top N.

## Output format

One-line header: date, time ET, filters applied, definitions used, data source.

| # | Ticker | Price | Gap % | PM Range % | Vol vs Baseline | Catalyst (time/date) | Key Levels | Setup (1–10) | Plan |
|---|---|---|---|---|---|---|---|---|---|

- **Key Levels:** e.g. "PDH 52.40 / PM high 51.90 / 50D 48.10".
- **Plan:** trigger, invalidation (stop), first target (e.g. "Long above PM high 51.90 on volume; stop 50.80; target 54").

After the table:
- **Earnings today/this week:** ⚠️ flag any names reporting soon.
- **Market context:** futures, key premarket macro events (data releases, Fed speakers) in 1–3 bullets.
- **Near misses:** names that barely failed the filters, if useful.
- If fewer than N pass, return only those that pass and say so. Never pad.

## Rules

- Premarket data is thin and volatile: state the data time and note when it's delayed.
- Never fabricate numbers, catalysts, or levels. Mark unverifiable values "n/a".
- Flag low-float or wide-spread names as higher risk.
- End with a one-line reminder that this is research, not financial advice; verify prices and levels and manage risk before trading.
