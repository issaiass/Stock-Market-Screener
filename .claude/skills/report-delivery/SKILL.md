---
name: report-delivery
description: Stage 5.2/5.3 of the premarket pipeline. Runs deliver.py to send the rendered HTML report by email (Resend), Telegram and Discord. Use when the user wants to send, test, or configure delivery of the premarket report.
---

# Report Delivery

```
.venv\Scripts\python .claude\skills\report-delivery\deliver.py reports\premarket_<date>.html [REPORT.md]
```

Sends to every configured channel; any channel with missing keys prints a "skipped" line. Each channel runs in its own try/except and the script always exits 0, so a scheduled pipeline never crashes on delivery.

| Channel | Keys in `.env` | What is sent |
|---|---|---|
| Email (Resend) | `RESEND_API_KEY`, `EMAIL_TO`, optional `EMAIL_FROM` | Full HTML as the body, subject `AI Premarket Report - <date>` |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Summary caption (Summary section of REPORT.md) plus the HTML file as a document |
| Discord | `DISCORD_WEBHOOK_URL` | Summary message plus the HTML file as an attachment |

Real environment variables win over `.env`. `.env.example` documents where to get each key. `.env` holds secrets: never print them, paste them into chat, or share the file.

## Setup

- **Resend:** key from https://resend.com/api-keys. The default sender `onboarding@resend.dev` only delivers to the account owner's email; verify a domain at https://resend.com/domains and set `EMAIL_FROM` to send elsewhere.
- **Telegram:** create a bot with @BotFather (`/newbot`), copy the token, message the bot once, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to read your chat id.
- **Discord:** channel settings, Integrations, Webhooks, New Webhook, Copy Webhook URL.

## Status

Real sends to email, Telegram and Discord have succeeded in a full pipeline run. The `--only` filter was tested with Telegram.

`--only email,telegram,discord` (extra argument to `deliver.py`) sends just those channels and prints `<channel> disabled (--only)` for the rest. `run_pipeline.py --send ...` passes it through.
