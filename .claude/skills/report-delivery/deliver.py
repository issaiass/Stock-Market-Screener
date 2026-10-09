#!/usr/bin/env python3
"""Deliver the premarket report: email (Resend), Telegram, Discord.
Usage: python deliver.py reports/premarket_<date>.html [REPORT.md] [--only email,telegram,discord]
Config from env vars or a local .env (env vars win). Each channel with missing keys is
skipped with a clear line. Nothing here ever crashes the pipeline: exit code is always 0.
  Email:    RESEND_API_KEY, EMAIL_TO, optional EMAIL_FROM
  Telegram: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  Discord:  DISCORD_WEBHOOK_URL
"""
import json
import os
import re
import sys
from pathlib import Path

import requests

KEYS = ("RESEND_API_KEY", "EMAIL_TO", "EMAIL_FROM", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
        "DISCORD_WEBHOOK_URL")
DEFAULT_FROM = "AI Premarket Analyst <onboarding@resend.dev>"


def load_env(path=".env"):
    """Tiny KEY=VALUE parser. Environment variables take priority."""
    vals = {}
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    for k in KEYS:
        if os.environ.get(k):
            vals[k] = os.environ[k]
    return vals


def short_summary(md_path, date):
    """Title plus the Summary section of REPORT.md, trimmed for chat apps."""
    text = Path(md_path).read_text(encoding="utf-8") if Path(md_path).exists() else ""
    m = re.search(r"^## [^\n]*\n(.*?)(?=^## )", text, re.S | re.M)  # first section = summary, any language
    body = m.group(1).strip() if m else "Full report attached."
    body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
    return f"AI Premarket Report - {date}\n\n{body}"[:1800]


def send_email(cfg, html, date):
    key, to = cfg.get("RESEND_API_KEY"), cfg.get("EMAIL_TO")
    if not key or not to:
        return "email skipped, set RESEND_API_KEY + EMAIL_TO"
    r = requests.post("https://api.resend.com/emails",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      data=json.dumps({"from": cfg.get("EMAIL_FROM") or DEFAULT_FROM,
                                       "to": [a.strip() for a in to.split(",") if a.strip()],
                                       "subject": f"AI Premarket Report - {date}", "html": html}),
                      timeout=30)
    return f"email sent to {to}" if r.ok else f"email failed, Resend {r.status_code}: {r.text[:200]}"


def send_telegram(cfg, report, summary):
    tok, chat = cfg.get("TELEGRAM_BOT_TOKEN"), cfg.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return "telegram skipped, set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID"
    base = f"https://api.telegram.org/bot{tok}"
    with report.open("rb") as f:  # summary as the document caption (1024 char limit), full HTML attached
        r = requests.post(f"{base}/sendDocument", data={"chat_id": chat, "caption": summary[:1000]},
                          files={"document": (report.name, f, "text/html")}, timeout=60)
    return "telegram sent" if r.ok else f"telegram failed, {r.status_code}: {r.text[:200]}"


def send_discord(cfg, report, summary):
    url = cfg.get("DISCORD_WEBHOOK_URL")
    if not url:
        return "discord skipped, set DISCORD_WEBHOOK_URL"
    with report.open("rb") as f:
        r = requests.post(url, data={"content": summary[:1900]},
                          files={"file": (report.name, f, "text/html")}, timeout=60)
    return "discord sent" if r.ok else f"discord failed, {r.status_code}: {r.text[:200]}"


def main():
    only = None  # --only email,telegram,discord : send just these (default: every channel with keys set)
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        only = {s.strip().lower() for s in sys.argv[i + 1].split(",")} if i + 1 < len(sys.argv) else set()
        del sys.argv[i:i + 2]
    if len(sys.argv) < 2:
        print("usage: python deliver.py reports/premarket_<date>.html [REPORT.md]")
        return 0
    report = Path(sys.argv[1])
    if not report.exists():
        print(f"delivery skipped, report not found: {report}")
        return 0
    cfg = load_env()
    m = re.search(r"\d{4}-\d{2}-\d{2}", report.name)
    date = m.group(0) if m else "latest"
    summary = short_summary(sys.argv[2] if len(sys.argv) > 2 else "REPORT.md", date)
    html = report.read_text(encoding="utf-8")
    for name, fn in (("email", lambda: send_email(cfg, html, date)),
                     ("telegram", lambda: send_telegram(cfg, report, summary)),
                     ("discord", lambda: send_discord(cfg, report, summary))):
        if only is not None and name not in only:
            print(f"{name} disabled (--only)")
            continue
        try:
            print(fn())
        except Exception as e:  # one channel failing never blocks the others
            print(f"{name} failed, {type(e).__name__}: {str(e)[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
