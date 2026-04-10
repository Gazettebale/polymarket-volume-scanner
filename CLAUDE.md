# CLAUDE.md — Polymarket Volume Scanner

## Project overview
Single-file Python/Flask dashboard for Polymarket manual trading.
All UI is a large HTML string inside `web_dashboard.py` with inline JS (no frontend build step).

## Stack
- **Backend**: Python 3.9+, Flask, Flask-SocketIO (port 8080)
- **Frontend**: Vanilla JS + inline CSS inside the `HTML` triple-quoted string in `web_dashboard.py`
- **APIs**: All public, no auth needed

## Run
```bash
python3 web_dashboard.py
# → http://localhost:8080
```

## Architecture
`web_dashboard.py` has 3 parts:
1. **Python backend** — Flask routes + background threads (scanner, sport, whales)
2. **HTML string** — the entire frontend (CSS + HTML + JS) as a Python triple-quoted string
3. **Flask routes** — `/` serves the HTML, `/api/markets` serves cached JSON

Background threads update `_cache` dict every 60s. Socket.IO pushes updates to all clients.

## 4 tabs
| Tab | Data source |
|-----|-------------|
| Top Marchés | `gamma-api` + `clob.polymarket.com` orderbooks |
| Sport du Jour | Same, filtered for sports in next 24h |
| Whale Tracker | `run_whale_tracker_api()` in polymarket_scanner.py |
| Leaderboard CLOB | `lb-api.polymarket.com` — client-side fetch, no Python needed |

## Important: Python string escaping in JS
The HTML is a Python `"""..."""` triple-quoted string. Rules:
- `\'` in Python → `'` in output (breaks JS single-quoted strings!)
- To get `\'` in JS output, use `\\'` in Python
- Avoid `\'` in JS inside the HTML string — use double quotes or `this.hidden=true` instead of `style.display=\'none\'`

## Leaderboard CLOB tab
Added in April 2026, integrated from a separate Next.js project (`polymarket-clob-leaderboard`).
All logic is client-side JS in `web_dashboard.py`:
- `lb` state object, `lbFetchPage`, `lbRenderTable`, `lbSearch`, `lbEstimateRank`, `lbFetchActivity`
- Rank estimation via log-log interpolation (same algorithm as original Next.js app)
- APIs: `lb-api.polymarket.com` (P&L/volume) + `data-api.polymarket.com` (fills)

## GitHub
Repo: `Gazettebale/polymarket-volume-scanner` (public)
