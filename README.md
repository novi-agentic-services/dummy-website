# dummy-website

Cloudflare-compatible static webpage with 6 dashboard blocks and auto-refreshing live metrics.

## Metrics shown

Top row:
- Total Tasks Completed
- Active Agents
- Tokens Used

Bottom row:
- Tokens Left
- Today Completed
- Queue Backlog

## How live data works

The page fetches JSON from `./metrics.json` every 15 seconds by default.

Expected payload shape:

```json
{
  "totalTasksCompleted": 152,
  "activeAgents": 3,
  "tokensUsed": 84200,
  "tokensLeft": 415800,
  "todayCompleted": 31,
  "queueBacklog": 9,
  "updatedAt": "2026-03-22T21:15:00Z"
}
```

## Optional runtime override

You can point to another endpoint (e.g., a Cloudflare Worker) by editing these constants in `index.html`:

```js
const METRICS_ENDPOINT = window.METRICS_ENDPOINT || './metrics.json';
const REFRESH_MS = Number(window.REFRESH_MS || 15000);
```

Set `METRICS_ENDPOINT` to your Worker URL when ready.

## Deploy on Cloudflare Pages

- Framework preset: **None**
- Build command: *(leave empty)*
- Build output directory: `/`

No build step is required.
