---
name: pick-scorer
description: Closes the loop on the premarket report. Scores yesterday's logged picks (trigger hit, stop, +1R/+2R, swing returns) against real price bars and summarizes results by conviction color, so the user can see whether conviction scores mean anything. Use when the user asks how past picks performed or whether the conviction scores are reliable.
---

# Pick Scorer

`run_pipeline.py` appends every pick to `logs/picks_log.csv` (date, ticker, list, conviction, price, trigger, stop, targets). `score_picks.py` scores the unscored rows against real bars.

```
.venv\Scripts\python .claude\skills\pick-scorer\score_picks.py
```

- **Day picks:** walks 5-minute bars of the pick date inside the 10:00 to 15:30 ET window. Trigger hit = first bar trading above the logged trigger. Then stop vs +1R vs +2R, whichever comes first (stop wins if both are in the same bar, the pessimistic reading). Result in R. No trigger = no trade.
- **Swing picks:** close-to-close return after 1 and 5 trading days versus the logged price (no stops or targets, per the criteria).
- **Output:** `logs/picks_scored.csv` plus a summary by list and conviction (n, trigger rate, win rate, average R or return).
- Only days older than today are scored. Yahoo 5-minute bars only go back about 60 days.

## Read it honestly

- Small samples mean nothing: wait for 30+ picks per conviction color before drawing conclusions.
- Fills are theoretical (at the trigger, no slippage, no scale-outs): it checks the idea, not your account.
- If green does not beat yellow and red over time, the conviction scoring is noise and the prompts need work.
- Educational only, not financial advice.
