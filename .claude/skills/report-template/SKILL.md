---
name: report-template
description: Stage 1 of the premarket report pipeline. Holds REPORT_TEMPLATE.md, the fixed 12-section blueprint (Claude Sonnet + Claude Haiku, independent passes) used by the analyst and merge prompts. Use when designing, editing, or filling the premarket report skeleton, or when writing analyst/merge prompts that must follow it.
---

# Report Template

`REPORT_TEMPLATE.md` (in this folder) is the single source of truth for the premarket report layout. Do not duplicate it elsewhere; reference its path.

## Sections, in order

1. Title + dated subtitle (Claude Sonnet + Claude Haiku, independent passes)
2. One-line disclaimer (rules pick the watchlist, both AIs judge quality, not financial advice)
3. Summary: the tape in one line, the catch we're watching, a one-line two-brain verdict
4. Pre-Market Gappers (each with its full catalyst headline)
5. Day Trading Watchlist: Ticker, Catalyst, Levels, Plan, Haiku check, Conviction
6. Swing Watchlist: Ticker, Catalyst, Trend context, Idea, Haiku check, Conviction
7. Market Trends of the Day
8. Technical Signals for Today
9. Economic Data, Rates and the Fed (from the econ calendar)
10. Coming Up (tomorrow's events and earnings)
11. Skips and Traps
12. Where the Two Brains Landed (agreement, rules vs discretion, each brain's sharp catch)

Conviction key: 🟢 high, 🟡 medium, 🔴 low. Voice: casual and plain-spoken. No em dashes.

## How to use it

- **Writing analyst prompts (later stages):** tell each analyst to fill every section in this order, using the exact column headers, and to leave the "Haiku check" column for the merge step. Feed the data from the `premarket-report` skill (gappers, econ events, upgrades, options flow, watchlist hits).
- **Writing the merge prompt:** merge Sonnet's and Haiku's independent passes into one document that follows the template exactly, fills "Haiku check" and section 12 from the real differences between passes, and does not smooth over disagreements.
- **Editing the template:** change `REPORT_TEMPLATE.md` only, then update any prompt that quotes section names.
- **Before delivering a filled report, check:** all 12 sections present and in order; gappers carry full headlines; every watchlist row has a conviction color; no em dashes (search for the character); no invented numbers.

## Notes

- Sections 5 and 6 map to the `premarket-report` Day Trading and Swing filters in its `config.json`.
- The report is research only, not financial advice.

## Example and second brain role

- `EXAMPLE_REPORT.md` (this folder) is a short, fictional, fully filled report. The pipeline shows it to the analyst and the merge editor as a format and tone reference. All content in it is fake: copy the structure, never the content.
- It ends with a machine-readable `<!--PICKS [...] -->` comment (ticker, list, conviction). The pipeline strips it from the report and logs the picks for `pick-scorer`.
- The Haiku column is a skeptic's view: its job is to find why a pick fails, not to repeat the analyst.
