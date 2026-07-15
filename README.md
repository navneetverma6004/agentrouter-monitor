# AgentRouter Uptime Monitor

Pings AgentRouter every 5 minutes from GitHub's free servers and pushes a
notification to your phone/laptop the moment it goes down, and again when
it recovers. No server of your own needed.

## 1. Set up push notifications (ntfy.sh) — 2 minutes

ntfy.sh is free, needs no account, and works via a "topic" name (like a
channel). Anyone who knows the topic name can post to it or read it, so
pick something long and random rather than "agentrouter-status".

1. Pick a topic, e.g. `agentrouter-jai-9f3k2x` (change the random part).
2. Install the ntfy app:
   - iOS: https://apps.apple.com/app/ntfy/id1625396347
   - Android: https://play.google.com/store/apps/details?id=io.heckel.ntfy
   - Desktop/browser: just open `https://ntfy.sh/agentrouter-jai-9f3k2x` and
     click "Subscribe" (or use the desktop app).
3. In the app, subscribe to your topic name. That's it — no login.

## 2. Create the GitHub repo

1. Create a new **private** repo on GitHub (private is fine, this workflow
   uses almost no Actions minutes).
2. Upload these two files, keeping the folder structure:
   - `monitor.py`
   - `.github/workflows/uptime-check.yml`

## 3. Add your secrets

In the repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `AGENTROUTER_API_KEY` | Your AgentRouter API key (from the console) |
| `NTFY_TOPIC` | The topic name you picked above, e.g. `agentrouter-jai-9f3k2x` |

## 4. Test it

Go to the **Actions** tab → "AgentRouter Uptime Monitor" → **Run workflow**
(manual trigger button). Check the run log — you should see a line like:

```
[2026-07-15 10:32:01] status=up (HTTP 200)
```

You won't get a notification on this first run (nothing changed from
"unknown"). To confirm notifications work end-to-end, temporarily break
the check — e.g. set `AGENTROUTER_API_KEY` secret to a garbage value,
re-run, confirm you get NO alert (since 401 is treated as "up, bad key"),
then put the real key back.

After that it runs automatically every 5 minutes forever, and you'll only
hear from it when the status actually changes.

## Notes / limitations

- GitHub's cron scheduler isn't millisecond-precise — under load it can lag
  a few minutes behind the schedule. Fine for "is it down right now"
  alerting, not for sub-minute SLA tracking.
- A `401/403/429` response is treated as "up" (the service answered — your
  key or quota is the problem, not an outage). If you'd rather treat auth
  errors as "down" too, remove that special case in `monitor.py`.
- Each check costs 1 token of usage against your AgentRouter quota (~288
  tiny requests/day). If you'd rather not spend any quota, you can instead
  point the check at any lighter endpoint AgentRouter exposes for status —
  worth asking them if one exists, since it wasn't documented.
- State (up/down) is kept in a GitHub Actions cache file between runs, so
  the very first run after setup always looks like a fresh start.
