#!/usr/bin/env python3
"""scan.py: collect raw premarket data into packet.json. ZERO analysis.
No conviction, no buckets, no opinions. Judgment happens later in AI prompts.
Only yfinance, feedparser, requests (zoneinfo is stdlib). Usage: python scan.py [out.json]
"""
import json, re, sys, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser, requests, yfinance as yf

ET = ZoneInfo("America/New_York")
UA = {"User-Agent": "Mozilla/5.0"}
ARGS = sys.argv[1:]
EXTRA = []  # --tickers NVDA,AMD,GLD: focus names added to the packet even if they did not gap
if "--tickers" in ARGS:
    i = ARGS.index("--tickers")
    EXTRA = [s.strip().upper() for s in ARGS[i + 1].split(",") if s.strip()] if i + 1 < len(ARGS) else []
    del ARGS[i:i + 2]
OUT = ARGS[0] if ARGS else "packet.json"
CACHE = Path(".econ_cache.json")
TOP_N, MIN_ABS_GAP, MIN_PRICE = 12, 4.0, 3.0

INDEXES = {"S&P 500": "^GSPC", "Dow": "^DJI", "Nasdaq": "^IXIC", "Russell 2000": "^RUT",
           "VIX": "^VIX", "US 10Y": "^TNX", "US 3M": "^IRX", "WTI Oil": "CL=F", "Dollar (DXY)": "DX-Y.NYB"}
UNIVERSE = ("NVDA AMD AVGO SMCI MRVL TSLA AAPL MSFT META AMZN GOOGL NFLX DELL SNOW PLTR COIN MSTR "
            "SOFI RIVN NIO MARA RIOT BA DIS JPM BAC XOM CVX HOOD UBER CRWD PANW CELH LULU NKE CAVA "
            "DKNG ARM INTC MU").split()
FEEDS = {
    "MarketWatch Top": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "MarketWatch RealTime": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News Markets": "https://news.google.com/rss/search?q=markets+earnings+when:1d&hl=en-US&gl=US&ceid=US:en",
}
PRIMARY = ["bloomberg", "reuters", "cnbc", "marketwatch", "barron", "yahoo finance", "wsj", "wall street journal",
           "financial times", "associated press"]
# NAME_STOP fix: generic company words are never a catalyst match on their own. A headline counts only if it
# names the ticker on a word boundary or holds a distinctive name token of 4+ letters, because words like
# "Applied" or "Digital" otherwise hit unrelated firms (Applied Optoelectronics vs Applied Digital).
NAME_STOP = set("""the inc corp corporation co company holdings holding technologies technology group digital applied
advanced strategy motors energy platforms systems international global limited ltd plc class common stock
shares american united first new national solutions services resources capital financial bank partners
industries brands entertainment therapeutics pharmaceuticals semiconductor networks software data""".split())


def log(m):
    print(m, flush=True)


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:  # one bad call never crashes the run
        log(f"  warn: {type(e).__name__}: {str(e)[:80]}")
        return default


def clean(x):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x or "")).strip()


def env_keys():
    """ALPACA_* keys from the environment or a .env in the working directory (optional)."""
    import os
    vals = {}
    if Path(".env").exists():
        for line in Path(".env").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return {k: os.environ.get(k) or vals.get(k) for k in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY")}


def alpaca_premarket_rvol(sym, day, keys):
    """True premarket RVOL from Alpaca's free IEX feed: today's 04:00-now volume vs the same window on prior
    sessions. IEX volume is a small share of the market, but the ratio is still comparable. Untested without keys."""
    from datetime import timedelta
    now = datetime.now(ET)
    start = datetime.combine(day - timedelta(days=9), datetime.min.time(), ET).astimezone(ZoneInfo("UTC"))
    r = requests.get(f"https://data.alpaca.markets/v2/stocks/{sym}/bars",
                     headers={"APCA-API-KEY-ID": keys["ALPACA_API_KEY_ID"],
                              "APCA-API-SECRET-KEY": keys["ALPACA_API_SECRET_KEY"]},
                     params={"timeframe": "5Min", "start": start.isoformat(), "feed": "iex", "limit": 10000},
                     timeout=20)
    r.raise_for_status()
    bars = r.json().get("bars") or []
    cutoff = now.strftime("%H:%M") if now.date() == day and "04:00" <= now.strftime("%H:%M") < "09:30" else "09:29"
    per_day = {}
    for b in bars:
        t = datetime.fromisoformat(b["t"].replace("Z", "+00:00")).astimezone(ET)
        if "04:00" <= t.strftime("%H:%M") <= cutoff:
            per_day[t.date()] = per_day.get(t.date(), 0) + b["v"]
    today_v = per_day.pop(day, 0)
    prior = [v for v in per_day.values() if v > 0][-5:]
    return (today_v / (sum(prior) / len(prior))) if prior else None


# 1) market snapshot
def snapshot():
    out = {}
    for name, sym in INDEXES.items():
        c = safe(lambda: yf.Ticker(sym).history(period="10d")["Close"].dropna())
        if c is not None and len(c) >= 2:
            last, prev = float(c.iloc[-1]), float(c.iloc[-2])
            out[name] = {"symbol": sym, "last": last, "prev_close": prev, "change_pct": (last / prev - 1) * 100}
        else:
            out[name] = {"symbol": sym, "last": None, "prev_close": None, "change_pct": None}
    return out


# 2) movers
def movers():
    rows = {}
    for key in ("day_gainers", "most_actives"):
        res = safe(lambda: yf.screen(key, count=100), {}) or {}
        for q in res.get("quotes", []):
            s = q.get("symbol")
            if s and s not in rows:
                pre = q.get("preMarketPrice")
                price = pre or q.get("regularMarketPrice")
                gap = q.get("preMarketChangePercent") if pre else q.get("regularMarketChangePercent")
                rows[s] = {"ticker": s, "name": q.get("shortName") or q.get("longName") or s, "price": price,
                           "prev_close": q.get("regularMarketPreviousClose"), "gap_pct": gap,
                           "gap_source": "preMarket" if pre else "regularMarket",
                           "market_cap": q.get("marketCap"), "volume": q.get("regularMarketVolume")}
    if len(rows) >= 5:
        return list(rows.values()), "yfinance_screeners"
    log("  live screeners returned < 5 names, using static UNIVERSE")
    out = []
    for s in UNIVERSE:
        t = yf.Ticker(s)
        c = safe(lambda: t.history(period="10d")["Close"].dropna())
        if c is None or len(c) < 2:
            continue
        info = safe(lambda: t.fast_info, {}) or {}
        out.append({"ticker": s, "name": s, "price": float(c.iloc[-1]), "prev_close": float(c.iloc[-2]),
                    "gap_pct": (float(c.iloc[-1]) / float(c.iloc[-2]) - 1) * 100, "gap_source": "daily_closes",
                    "market_cap": safe(lambda: info["market_cap"]), "volume": safe(lambda: info["last_volume"])})
    return out, "static_universe"


# 4) market news
def market_news():
    items = []
    for src, url in FEEDS.items():
        r = safe(lambda: requests.get(url, headers=UA, timeout=15))
        if r is None or not r.ok:
            continue
        for e in feedparser.parse(r.content).entries[:40]:
            title = clean(e.get("title"))
            if re.search(r"price prediction|20\d\d\s*[-–]\s*20\d\d", title, re.I):
                continue
            items.append({"source": src, "title": title, "summary": clean(e.get("summary"))[:300],
                          "published": e.get("published", ""), "link": e.get("link", "")})
    return items


# 5) economic calendar
def econ_calendar():
    now = datetime.now(ET)
    today, tomorrow = now.date(), now.date().fromordinal(now.date().toordinal() + 1)
    cal = {"source": "ForexFactory this-week JSON (nfs.faireconomy.media)", "filter": "country=USD, impact=High",
           "today_date": str(today), "tomorrow_date": str(tomorrow), "today": [], "tomorrow": []}
    try:
        raw, note = None, None
        cached = json.loads(CACHE.read_text()) if CACHE.exists() else None
        if cached and time.time() - cached["fetched_at"] < 4 * 3600:
            raw = cached["data"]
        else:
            r = safe(lambda: requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json",
                                          headers=UA, timeout=15))
            if r is not None and r.ok:
                raw = r.json()
                CACHE.write_text(json.dumps({"fetched_at": time.time(), "data": raw}))
            elif cached:
                raw, note = cached["data"], "live fetch failed, used last cached week"
        if note:
            cal["note"] = note
        for ev in raw or []:
            if ev.get("country") != "USD" or ev.get("impact") != "High":
                continue
            t = datetime.fromisoformat(ev["date"]).astimezone(ET)
            row = {"time_et": t.strftime("%H:%M"), "title": ev.get("title"),
                   "forecast": ev.get("forecast"), "previous": ev.get("previous")}
            if t.date() == today:
                cal["today"].append(row)
            elif t.date() == tomorrow:
                cal["tomorrow"].append(row)
        for k in ("today", "tomorrow"):
            cal[k].sort(key=lambda e: e["time_et"])
        if raw is None:
            cal["error"] = "no calendar data available"
    except Exception as e:
        cal["error"] = f"{type(e).__name__}: {str(e)[:80]}"
    return cal


# 6) per-gapper enrichment
def name_tokens(name):
    return [w for w in re.findall(r"[A-Za-z]+", name or "") if len(w) >= 4 and w.lower() not in NAME_STOP]


def matches(title, ticker, name):
    if re.search(rf"\b{re.escape(ticker)}\b", title):
        return True
    return any(re.search(rf"\b{re.escape(w)}\b", title, re.I) for w in name_tokens(name))


def publisher_rank(pub):
    p = (pub or "").lower()
    return next((i for i, k in enumerate(PRIMARY) if k in p), len(PRIMARY))


def headlines(t, ticker, name, rss):
    found = []
    for n in safe(lambda: t.news, []) or []:
        c = n.get("content", n)
        title = clean(c.get("title"))
        pub = (c.get("provider") or {}).get("displayName") or c.get("publisher") or ""
        url = ((c.get("canonicalUrl") or {}).get("url")) or c.get("link") or ""
        if title and matches(title, ticker, name):
            found.append({"title": title, "publisher": pub, "published": c.get("pubDate") or "", "link": url})
    for n in rss:
        if matches(n["title"], ticker, name):
            found.append({"title": n["title"], "publisher": n["source"], "published": n["published"], "link": n["link"]})
    # Per-ticker Google News RSS (keyless): yfinance per-ticker news often comes back empty.
    from urllib.parse import quote
    q = quote(f'{ticker} stock {" ".join(name_tokens(name)[:2])} when:2d')
    r = safe(lambda: requests.get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en",
                                  headers=UA, timeout=15))
    for e in (feedparser.parse(r.content).entries[:15] if r is not None and r.ok else []):
        full = clean(e.get("title"))
        title, _, pub = full.rpartition(" - ")
        if not title:
            title, pub = full, ""
        if re.search(r"price prediction|20\d\d\s*[-–]\s*20\d\d", title, re.I):
            continue
        if matches(title, ticker, name):
            found.append({"title": title, "publisher": pub or "Google News", "published": e.get("published", ""),
                          "link": e.get("link", "")})
    seen, out = set(), []
    for h in sorted(found, key=lambda h: publisher_rank(h["publisher"])):
        if h["title"].lower() not in seen:
            seen.add(h["title"].lower())
            out.append(h)
    return out[:8]


def levels(t):
    """5-min bars incl. extended hours. NOTE: yfinance reports about 0 premarket volume, so a true
    premarket RVOL needs a premarket feed (e.g. Alpaca); full-day relative volume is the keyless stand-in."""
    h = safe(lambda: t.history(period="5d", interval="5m", prepost=True))
    if h is None or h.empty:
        return {}, None
    h.index = h.index.tz_convert(ET)
    day = h.index[-1].date()
    d = h[h.index.date == day]
    pre = d.between_time("04:00", "09:29")
    reg = d.between_time("09:30", "15:59")
    tp = (d["High"] + d["Low"] + d["Close"]) / 3
    vol = float(d["Volume"].sum())
    return {"session_date": str(day), "last_bar_close": float(d["Close"].iloc[-1]),
            "vwap": float((tp * d["Volume"]).sum() / vol) if vol else None,
            "hod": float(d["High"].max()), "lod": float(d["Low"].min()),
            "premarket_high": float(pre["High"].max()) if len(pre) else None,
            "premarket_volume": float(pre["Volume"].sum()) if len(pre) else None,
            "open": float(reg["Open"].iloc[0]) if len(reg) else None,
            "day_volume": vol}, day


def daily(t, session_day):
    h = safe(lambda: t.history(period="1y", interval="1d"))
    if h is None or h.empty:
        return {}
    h = h[[i.date() < session_day for i in h.index]] if session_day else h  # drop today's partial bar
    if len(h) < 2:
        return {}
    return {"prior_close": float(h["Close"].iloc[-1]), "prior_high": float(h["High"].iloc[-1]),
            "sma200": float(h["Close"].tail(200).mean()) if len(h) >= 200 else None,
            "avg_vol_20d": float(h["Volume"].tail(20).mean())}


def next_earnings(t, session_day):
    cal = safe(lambda: t.calendar, {}) or {}
    dates = [d for d in (cal.get("Earnings Date") or []) if d >= session_day] if isinstance(cal, dict) else []
    return str(min(dates)) if dates else None


def analyst_changes(t, day):
    from datetime import timedelta
    u = safe(lambda: t.upgrades_downgrades)
    if u is None or u.empty:
        return []
    cutoff = day - timedelta(days=3)
    out = []
    for dt, r in u.iterrows():
        if dt.date() >= cutoff:
            out.append({"date": str(dt.date()), "firm": r.get("Firm"), "from": r.get("FromGrade") or None,
                        "to": r.get("ToGrade"), "action": r.get("Action"),
                        "price_target_action": r.get("priceTargetAction") or None,
                        "price_target": float(r["currentPriceTarget"]) if r.get("currentPriceTarget") else None})
    return out[:6]


def options_summary(t):
    """Nearest expiry only. A simple summary, not sweep or block data."""
    exp = safe(lambda: t.options, ()) or ()
    if not exp:
        return None
    ch = t.option_chain(exp[0])
    cv, pv = float(ch.calls["volume"].sum()), float(ch.puts["volume"].sum())
    top = ch.calls.sort_values("volume", ascending=False).head(1)
    row = top.iloc[0] if len(top) else None
    return {"expiry": exp[0], "call_volume": cv, "put_volume": pv,
            "call_put_ratio": round(cv / pv, 2) if pv else None,
            "call_oi": float(ch.calls["openInterest"].sum()), "put_oi": float(ch.puts["openInterest"].sum()),
            "top_call_strike": float(row["strike"]) if row is not None else None,
            "top_call_volume": float(row["volume"]) if row is not None else None,
            "top_call_vol_gt_oi": bool(row is not None and row["openInterest"] and row["volume"] > row["openInterest"])}


def trade_plan(lv, price):
    """Trend Join Long numbers computed in code so the AI judges instead of calculating."""
    pmh, hod, lod = lv.get("premarket_high"), lv.get("hod"), lv.get("lod")
    if not (pmh and hod and lod):
        return None, None
    trigger, stop = max(pmh, hod), min(pmh * 0.99, lod)
    r = trigger - stop
    pos = {"vs_vwap_pct": round((price / lv["vwap"] - 1) * 100, 2) if price and lv.get("vwap") else None,
           "dist_to_pmh_pct": round((pmh / price - 1) * 100, 2) if price else None,
           "dist_to_hod_pct": round((hod / price - 1) * 100, 2) if price else None}
    if r <= 0:
        return None, pos
    return {"trigger": round(trigger, 2), "stop": round(stop, 2), "r": round(r, 2),
            "r_pct": round(r / trigger * 100, 2), "target_1r": round(trigger + r, 2),
            "target_2r": round(trigger + 2 * r, 2), "window": "10:00-15:30 ET", "flat_by": "15:51 ET"}, pos


def enrich(g, rss):
    t = yf.Ticker(g["ticker"])
    lv, day = safe(lambda: levels(t), ({}, None))
    dm = safe(lambda: daily(t, day), {}) or {}
    g.update({"levels": lv, "daily": dm})
    vol = lv.get("day_volume") or g.get("volume")
    g["rvol"] = (vol / dm["avg_vol_20d"]) if vol and dm.get("avg_vol_20d") else None
    g["rvol_basis"] = "full_day_yahoo"
    g["rvol_note"] = "full-day relative volume (yfinance has no premarket volume)"
    g["premarket_rvol"] = None
    keys = env_keys()
    if all(keys.values()) and day:  # optional: true premarket RVOL from Alpaca's free IEX feed
        g["premarket_rvol"] = safe(lambda: alpaca_premarket_rvol(g["ticker"], day, keys))
        if g["premarket_rvol"] is not None:
            g["rvol_basis"], g["rvol_note"] = "alpaca_iex_premarket", "premarket volume vs same window on prior sessions"
    rv = g["premarket_rvol"] if g["premarket_rvol"] is not None else g["rvol"]
    g["plan"], g["position"] = trade_plan(lv, g.get("price"))
    g["analyst_changes"] = safe(lambda: analyst_changes(t, day or datetime.now(ET).date()), []) or []
    g["options"] = safe(lambda: options_summary(t))
    g["next_earnings"] = safe(lambda: next_earnings(t, day or datetime.now(ET).date()))
    g["headlines"] = headlines(t, g["ticker"], g["name"], rss)
    g["catalyst_found"] = bool(g["headlines"])
    g["earnings_on_gap_day"] = bool(day and g["next_earnings"] == str(day))
    # 7) deterministic eligibility flags (WATCHLIST_CRITERIA.md)
    p, gap, mc = g.get("price"), g.get("gap_pct"), g.get("market_cap")
    ph, sma = dm.get("prior_high"), dm.get("sma200")
    opn = lv.get("open") or p  # before the bell, premarket price stands in for the open
    g["open_is_proxy"] = not lv.get("open")
    ok = lambda *v: all(x is not None for x in v)
    g["day_eligible"] = bool(ok(gap, p, mc, rv, ph) and gap > 3 and p > 3 and mc > 1e9
                             and rv > 1.5 and p > ph)
    g["swing_eligible"] = bool(ok(gap, p, mc, opn, ph, sma) and gap >= 8 and p > 3 and opn > ph
                               and opn > sma and mc >= 8e8 and (g["catalyst_found"] or g["earnings_on_gap_day"]))
    g["swing_catalyst_type"] = "earnings" if g["earnings_on_gap_day"] else ("news" if g["catalyst_found"] else None)
    return g


def main():
    log("market snapshot..."); snap = snapshot()
    log("movers..."); rows, source = movers()
    gappers = [r for r in rows if r["gap_pct"] is not None and r["price"] and abs(r["gap_pct"]) >= MIN_ABS_GAP
               and r["price"] >= MIN_PRICE]
    gappers = sorted(gappers, key=lambda r: -abs(r["gap_pct"]))[:TOP_N]
    for g in gappers:
        g["focus"] = False
    have = {g["ticker"] for g in gappers}
    for s in EXTRA:  # user-requested names: added regardless of the gap filter, flagged focus
        if s in have:
            next(g for g in gappers if g["ticker"] == s)["focus"] = True
            continue
        info = safe(lambda: yf.Ticker(s).info, {}) or {}
        price = info.get("preMarketPrice") or info.get("regularMarketPrice") or info.get("currentPrice")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        gappers.append({"ticker": s, "name": info.get("shortName") or s, "price": price, "prev_close": prev,
                        "gap_pct": (price / prev - 1) * 100 if price and prev else None,
                        "gap_source": "focus_request", "market_cap": info.get("marketCap"),
                        "volume": info.get("regularMarketVolume"), "focus": True})
    log(f"{len(rows)} movers, {len(gappers)} names after gap filter and focus tickers ({source})")
    log("news..."); news = market_news()
    log("econ calendar..."); cal = econ_calendar()
    for i, g in enumerate(gappers, 1):
        log(f"enriching {g['ticker']} ({i}/{len(gappers)})")
        safe(lambda: enrich(g, news))
    now = datetime.now(ET)
    packet = {
        "generated_at": now.isoformat(), "candidate_source": source,
        "trading_day_note": ("Weekend, session data is from the last trading day." if now.weekday() >= 5
                             else "Weekday run. Before 9:30 ET the open is a premarket-price proxy."),
        "scan_params": {"min_abs_gap_pct": MIN_ABS_GAP, "min_price": MIN_PRICE, "top_n": TOP_N},
        "criteria": {
            "day_trading": "gap > 3%, price > $3, market cap > $1B, RVOL > 1.5, price above prior-day high (all required)",
            "swing": "gap >= 8%, price > $3, open > prior-day high, open > 200-day SMA, market cap >= $800M, "
                     "real catalyst: earnings on gap day, or news with no earnings (all required)"},
        "market_snapshot": snap, "econ_calendar": cal, "gappers": gappers, "market_news": news[:20],
        "gaps_to_fill": ["Market-wide earnings calendar is only partial (per-ticker next earnings date only).",
                         "Intraday levels need intraday bars; yfinance 5m data can be delayed or empty.",
                         "Premarket RVOL caveat: yfinance reports about 0 premarket volume, rvol is full-day vs 20-day average.",
                         "Market cap and screener fields are Yahoo snapshots and may lag."]}
    Path(OUT).write_text(json.dumps(packet, indent=2, default=str))
    log(f"wrote {OUT}: {len(gappers)} gappers, {len(news[:20])} news items")


if __name__ == "__main__":
    main()
