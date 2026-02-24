# quick_updates

Automatically tracks and logs service incidents from the [OpenAI Status Page](https://status.openai.com/).

Whenever a new incident is detected, it prints the affected product and latest status message to the console.

## Run locally

**1. Install dependencies**
```bash
pip install aiohttp
```

**2. Run**
```bash
python webhook_receiver.py
```

**Expected output**
```
Tracker is Up
```

When a new incident is detected:
```
[2026-02-25 10:32:00] Product: OpenAI API - Chat Completions
Status: Elevated error rates — Investigating (Minor impact)
Message - We are investigating elevated error rates affecting Chat Completions.
------------------------------------------------------------
```
