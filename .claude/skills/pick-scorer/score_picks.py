#!/usr/bin/env python3
"""Score logged premarket picks against real bars.
Usage: python score_picks.py        (reads logs/picks_log.csv, writes logs/picks_scored.csv, prints a summary)
Day picks: 5-minute bars of the pick date, 10:00-15:30 ET. Trigger = first bar whose high is above the
trigger; then stop vs +1R vs +2R, whichever comes first (stop wins within the same bar). Result in R.
Swing picks: close-to-close return after 1 and 5 trading days versus the logged price.
Fills are theoretical (at the trigger, no slippage, no scale-outs). Yahoo 5m bars reach back about 60 days.
"""
import csv
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf

ET = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[3]
LOG, OUT = ROOT / "logs" / "picks_log.csv", ROOT / "logs" / "picks_scored.csv"
FIELDS = ["date", "ticker", "list", "conviction", "price", "trigger", "stop", "target_1r", "target_2r",
          "result", "r", "ret_1d", "ret_5d"]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def score_day(row):
    trig, stop, t1, t2 = (f(row[k]) for k in ("trigger", "stop", "target_1r", "target_2r"))
    if None in (trig, stop, t1, t2):
        return "no_plan", None
    d = datetime.strptime(row["date"], "%Y-%m-%d").date()
    h = yf.Ticker(row["ticker"]).history(start=d, end=date.fromordinal(d.toordinal() + 1), interval="5m")
    if h.empty:
        return "no_data", None
    h.index = h.index.tz_convert(ET)
    h = h.between_time("10:00", "15:30")
    entered = False
    r = trig - stop
    for _, b in h.iterrows():
        if not entered:
            if b["High"] > trig:
                entered = True
                # same bar can also hit stop or targets: treat the bar pessimistically
                if b["Low"] <= stop:
                    return "stop", -1.0
                if b["High"] >= t2:
                    return "target_2r", 2.0
                if b["High"] >= t1:
                    return "target_1r", 1.0
            continue
        if b["Low"] <= stop:
            return "stop", -1.0
        if b["High"] >= t2:
            return "target_2r", 2.0
        if b["High"] >= t1:
            return "target_1r", 1.0
    if not entered:
        return "no_trigger", None
    return "open_at_close", round((float(h["Close"].iloc[-1]) - trig) / r, 2)


def score_swing(row):
    price = f(row["price"])
    d = datetime.strptime(row["date"], "%Y-%m-%d").date()
    h = yf.Ticker(row["ticker"]).history(start=d, end=date.fromordinal(d.toordinal() + 12), interval="1d")
    if price is None or len(h) < 2:
        return None, None
    closes = list(h["Close"])
    ret = lambda i: round((closes[i] / price - 1) * 100, 2) if len(closes) > i else None
    return ret(1), ret(5)


def main():
    if not LOG.exists():
        print("no logs/picks_log.csv yet: run the pipeline first")
        return 0
    done = set()
    if OUT.exists():
        done = {(r["date"], r["ticker"], r["list"]) for r in csv.DictReader(OUT.open(encoding="utf-8"))}
    today = date.today().isoformat()
    new = []
    for row in csv.DictReader(LOG.open(encoding="utf-8")):
        key = (row["date"], row["ticker"], row["list"])
        if key in done or row["date"] >= today:
            continue
        try:
            if row["list"] == "day":
                res, r = score_day(row)
                new.append({**row, "result": res, "r": r, "ret_1d": "", "ret_5d": ""})
            else:
                r1, r5 = score_swing(row)
                new.append({**row, "result": "swing", "r": "", "ret_1d": r1, "ret_5d": r5})
        except Exception as e:
            print(f"skip {key}: {type(e).__name__}: {str(e)[:80]}")
    if new:
        write_header = not OUT.exists()
        with OUT.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            if write_header:
                w.writeheader()
            w.writerows(new)
    rows = list(csv.DictReader(OUT.open(encoding="utf-8"))) if OUT.exists() else []
    print(f"scored {len(new)} new picks, {len(rows)} total\n")
    for lst in ("day", "swing"):
        for conv in ("green", "yellow", "red"):
            sub = [r for r in rows if r["list"] == lst and r["conviction"] == conv]
            if not sub:
                continue
            if lst == "day":
                trig = [r for r in sub if r["result"] not in ("no_trigger", "no_plan", "no_data")]
                rs = [float(r["r"]) for r in trig if r["r"] not in ("", "None")]
                wins = sum(1 for x in rs if x > 0)
                print(f"day   {conv:6} n={len(sub):3} triggered={len(trig):3} "
                      f"win%={100 * wins / len(rs):.0f} avgR={sum(rs) / len(rs):+.2f}" if rs else
                      f"day   {conv:6} n={len(sub):3} triggered=0")
            else:
                r5 = [float(r["ret_5d"]) for r in sub if r["ret_5d"] not in ("", "None")]
                print(f"swing {conv:6} n={len(sub):3} avg5d={sum(r5) / len(r5):+.2f}%" if r5 else
                      f"swing {conv:6} n={len(sub):3} no 5d data yet")
    print("\nSmall samples mean nothing: wait for 30+ picks per color. Educational only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
