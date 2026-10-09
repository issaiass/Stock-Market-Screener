#!/usr/bin/env python3
"""Premarket report: gappers, economic events, analyst upgrades, options flow.

Free sources only: Yahoo Finance (via yfinance) and the Forex Factory weekly
calendar JSON. Filters live in config.json next to this script.

Usage:  python premarket_report.py [--config config.json] [--out-dir reports]
Schedule it for ~8:35-8:40 ET so the report is ready by 8:45 ET.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf
from yfinance import EquityQuery

ET = ZoneInfo("America/New_York")
CAL_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- universe
def fetch_universe(cfg):
    """Page through US equities above the market-cap/price floor; Yahoo quote
    dicts include preMarketPrice / preMarketChangePercent when available."""
    u = cfg["universe"]
    q = EquityQuery("and", [
        EquityQuery("eq", ["region", "us"]),
        EquityQuery("is-in", ["exchange", "NMS", "NYQ", "ASE"]),
        EquityQuery("gt", ["intradaymarketcap", u["min_market_cap"]]),
        EquityQuery("gt", ["intradayprice", u["min_price"] - 0.5]),
    ])
    rows = []
    for page in range(u["max_pages"]):
        try:
            res = yf.screen(q, size=250, offset=page * 250,
                            sortField="intradaymarketcap", sortAsc=False)
        except Exception as e:  # noqa: BLE001
            log(f"screener page {page} failed: {e}")
            break
        quotes = res.get("quotes", [])
        rows += quotes
        if len(quotes) < 250:
            break
    for t in u.get("extra_tickers", []):
        try:
            rows.append(yf.Ticker(t).info | {"symbol": t})
        except Exception:  # noqa: BLE001
            pass
    return rows


def fill_premarket_prices(rows, chunk=200):
    """Fallback when screener quotes lack preMarketPrice: batch-download the
    latest 1m bar (incl. extended hours) for rows missing it."""
    missing = [r for r in rows if not r.get("preMarketPrice")]
    for i in range(0, len(missing), chunk):
        part = missing[i:i + chunk]
        try:
            px = yf.download([r["symbol"] for r in part], period="1d", interval="1m",
                             prepost=True, progress=False, group_by="ticker", threads=True)
        except Exception as e:  # noqa: BLE001
            log(f"batch download failed: {e}")
            continue
        for r in part:
            try:
                last = px[r["symbol"]]["Close"].dropna()
                if len(last):
                    r["preMarketPrice"] = float(last.iloc[-1])
            except Exception:  # noqa: BLE001
                pass


def stage1(rows, cfg):
    """Cheap pass: premarket price and gap vs prior close."""
    with_pre = sum(1 for r in rows if r.get("preMarketPrice"))
    if with_pre < 0.05 * max(len(rows), 1):
        log("screener lacks premarket prices; using batch 1m download fallback")
        fill_premarket_prices(rows)
    gap_floor = min(w["min_gap_pct"] for w in cfg["watchlists"].values())
    out = []
    for r in rows:
        pre = r.get("preMarketPrice")
        prev = r.get("regularMarketPreviousClose")
        if not pre or not prev:
            continue
        gap = (pre / prev - 1) * 100
        if gap >= gap_floor:
            out.append({"symbol": r["symbol"], "name": r.get("shortName", ""),
                        "pre": pre, "prev_close": prev, "gap": gap,
                        "mcap": r.get("marketCap") or 0})
    return out


# ------------------------------------------------------------- enrichment
def premarket_rvol(sym, now_et):
    """Premarket volume so far vs average of the same window (4:00 -> now) over
    prior sessions in the last ~7 days of 1m bars."""
    h = yf.Ticker(sym).history(period="7d", interval="1m", prepost=True)
    if h.empty:
        return None, None
    h.index = h.index.tz_convert(ET)
    today = now_et.date()
    cutoff = now_et.time()
    vols = {}
    for d, g in h.groupby(h.index.date):
        w = g.between_time("04:00", cutoff.strftime("%H:%M"))
        vols[d] = w["Volume"].sum()
    today_vol = vols.pop(today, None)
    prior = [v for v in vols.values() if v > 0]
    if today_vol is None or not prior:
        return today_vol, None
    return today_vol, today_vol / (sum(prior) / len(prior))


def earnings_today(tk, today):
    try:
        cal = tk.calendar
        dates = cal.get("Earnings Date", []) if isinstance(cal, dict) else []
        return any(d == today for d in dates)
    except Exception:  # noqa: BLE001
        return False


def latest_news(tk, hours, now_et):
    try:
        items = tk.news or []
    except Exception:  # noqa: BLE001
        return None
    best = None
    for it in items:
        c = it.get("content", it)
        title = c.get("title")
        ts = c.get("pubDate") or c.get("providerPublishTime")
        if not title or not ts:
            continue
        if isinstance(ts, (int, float)):
            t = datetime.fromtimestamp(ts, ET)
        else:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(ET)
        if now_et - t <= timedelta(hours=hours):
            if best is None or t > best[0]:
                best = (t, title)
    return best[1] if best else None


def enrich(c, cfg, now_et):
    sym = c["symbol"]
    tk = yf.Ticker(sym)
    d = tk.history(period="14mo", interval="1d")
    if d.empty:
        return None
    d.index = d.index.tz_localize(None) if d.index.tz is None else d.index.tz_convert(ET).tz_localize(None)
    d = d[d.index.date < now_et.date()]  # completed sessions only
    if len(d) < 2:
        return None
    c["prior_high"] = float(d["High"].iloc[-1])
    c["sma200"] = float(d["Close"].tail(200).mean()) if len(d) >= 200 else None
    c["pm_vol"], c["rvol"] = premarket_rvol(sym, now_et)
    c["earnings_today"] = earnings_today(tk, now_et.date())
    c["headline"] = latest_news(tk, cfg["report"]["news_lookback_hours"], now_et)
    c["tk"] = tk
    return c


# ---------------------------------------------------------------- filters
def check_day(c, f):
    return (c["gap"] > f["min_gap_pct"] and c["pre"] > f["min_price"]
            and c["mcap"] > f["min_market_cap"]
            and (c["rvol"] or 0) > f["min_premarket_rvol"]
            and (not f["require_above_prior_high"] or c["pre"] > c["prior_high"]))


def check_swing(c, f):
    ok = (c["gap"] >= f["min_gap_pct"] and c["pre"] > f["min_price"]
          and c["mcap"] >= f["min_market_cap"])
    if f["require_above_prior_high"]:
        ok = ok and c["pre"] > c["prior_high"]
    if f["require_above_sma200"]:
        ok = ok and c["sma200"] is not None and c["pre"] > c["sma200"]
    if f["require_catalyst"]:
        ok = ok and (c["earnings_today"] or c["headline"] is not None)
    return ok


# --------------------------------------------------------- other sections
def econ_events(cfg, now_et):
    r = cfg["report"]
    try:
        data = requests.get(CAL_URL, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"}).json()
    except Exception as e:  # noqa: BLE001
        return [f"Economic calendar unavailable ({e})"]
    out = []
    for ev in data:
        t = datetime.fromisoformat(ev["date"]).astimezone(ET)
        if t.date() != now_et.date():
            continue
        if ev["country"] not in r["econ_countries"] or ev["impact"] not in r["econ_impacts"]:
            continue
        out.append((t, f"{t:%H:%M} ET  [{ev['impact'][0]}] {ev['title']}"
                       f"  (fcst {ev.get('forecast') or '-'}, prev {ev.get('previous') or '-'})"))
    return [s for _, s in sorted(out)] or ["No medium/high-impact US events today."]


def upgrades(syms, now_et):
    out = []
    for s in syms:
        try:
            u = yf.Ticker(s).upgrades_downgrades
        except Exception:  # noqa: BLE001
            continue
        if u is None or u.empty:
            continue
        u = u[u.index >= pd.Timestamp(now_et.date() - timedelta(days=1)).tz_localize(u.index.tz)]
        for dt, row in u.iterrows():
            if row.get("Action") in ("up", "down", "init"):
                out.append(f"{s:6} {row['Firm']}: {row['FromGrade'] or '-'} -> {row['ToGrade']} "
                           f"({row['Action']}, {dt:%m-%d})")
    return out or ["No analyst rating changes found for tickers in this report."]


def options_flow(syms):
    out = []
    for s in syms:
        try:
            tk = yf.Ticker(s)
            exp = tk.options
            if not exp:
                continue
            ch = tk.option_chain(exp[0])
            cv, pv = ch.calls["volume"].sum(), ch.puts["volume"].sum()
            coi, poi = ch.calls["openInterest"].sum(), ch.puts["openInterest"].sum()
            top = ch.calls.sort_values("volume", ascending=False).head(1)
            hot = ""
            if len(top) and top["openInterest"].iloc[0] and top["volume"].iloc[0] > top["openInterest"].iloc[0]:
                hot = f"  hot call {top['strike'].iloc[0]:g} vol>{'OI'}"
            out.append(f"{s:6} exp {exp[0]}  C/P vol {cv:,.0f}/{pv:,.0f} "
                       f"(ratio {cv / pv if pv else float('inf'):.2f})  OI {coi:,.0f}/{poi:,.0f}{hot}")
        except Exception:  # noqa: BLE001
            continue
    return out or ["No options data available."]


# ----------------------------------------------------------------- report
def row(c, tag):
    cat = "EARNINGS today" if c["earnings_today"] else (c["headline"] or "n/a")
    if c["earnings_today"] and c["headline"]:
        cat += f" | {c['headline']}"
    return (f"{c['symbol']:6} {c['gap']:+6.1f}%  ${c['pre']:<9.2f} {tag:<12} {cat}")


def main():
    here = Path(__file__).parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(here / "config.json"))
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    now = datetime.now(ET)

    log("Fetching universe...")
    cands = stage1(fetch_universe(cfg), cfg)
    log(f"{len(cands)} gappers pass the gap floor; enriching...")
    enriched = [e for e in (enrich(c, cfg, now) for c in cands) if e]

    day = [c for c in enriched if check_day(c, cfg["watchlists"]["day_trading"])]
    swing = [c for c in enriched if check_swing(c, cfg["watchlists"]["swing"])]
    hits = {}
    for c in day:
        hits.setdefault(c["symbol"], [c, []])[1].append("DAY")
    for c in swing:
        hits.setdefault(c["symbol"], [c, []])[1].append("SWING")

    L = [f"PREMARKET REPORT  {now:%a %Y-%m-%d %H:%M} ET", "=" * 78, ""]
    L += ["ECONOMIC EVENTS (US, today)", "-" * 78, *econ_events(cfg, now), ""]
    L += ["QUALIFYING TICKERS", "-" * 78,
          f"{'TICKER':6} {'GAP':>7}  {'PRICE':<10} {'WATCHLIST':<12} CATALYST"]
    if hits:
        for c, tags in sorted(hits.values(), key=lambda x: -x[0]["gap"]):
            L.append(row(c, "+".join(tags)))
    else:
        L.append("None met all filters this morning.")
    L.append("")
    near = sorted(enriched, key=lambda c: -c["gap"])[:10]
    L += ["TOP GAPPERS (context, unfiltered)", "-" * 78]
    for c in near:
        rv = f"{c['rvol']:.1f}x" if c["rvol"] else "n/a"
        L.append(f"{c['symbol']:6} {c['gap']:+6.1f}%  ${c['pre']:<9.2f} RVOL {rv:<6} "
                 f"{'>PDH' if c['pre'] > c['prior_high'] else '<PDH'}  {c['headline'] or ''}")
    watch = [c["symbol"] for c in near] + list(hits)
    watch = list(dict.fromkeys(watch))
    L += ["", "ANALYST UPGRADES / DOWNGRADES (last 24h)", "-" * 78, *upgrades(watch, now), ""]
    flow_syms = list(hits) + [s for s in watch if s not in hits]
    L += ["OPTIONS FLOW (nearest expiry)", "-" * 78,
          *options_flow(flow_syms[:cfg["report"]["options_flow_top_n"]]), ""]
    L += ["Filters: " + json.dumps(cfg["watchlists"]),
          "Notes: premarket price stands in for the open; premarket RVOL is vs the same "
          "4:00-now window over prior ~5 sessions; free Yahoo data may be delayed or incomplete. "
          "Research only, not financial advice."]
    text = "\n".join(L)

    out_dir = Path(a.out_dir or cfg["report"]["output_dir"])
    if not out_dir.is_absolute():
        out_dir = here / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"premarket_{now:%Y-%m-%d}.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
