#!/usr/bin/env python3
"""
Polymarket Volume Scanner — Dashboard Web
Lance avec : python3 web_dashboard.py
Ouvre : http://localhost:5000
"""

import json
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string

from config import WATCH_INTERVAL_SECONDS
from polymarket_scanner import run_scanner, MarketOpportunity

app = Flask(__name__)

# Cache global — mis à jour en background toutes les 60s
_cache = {"markets": [], "last_update": None, "loading": True}
_lock  = threading.Lock()


# ─── Background scanner ───────────────────────────────────────────────────────
def background_scan():
    while True:
        try:
            markets = run_scanner(top_n=20, verbose=False)
            with _lock:
                _cache["markets"]     = [_serialize(m) for m in markets]
                _cache["last_update"] = datetime.now().strftime("%H:%M:%S")
                _cache["loading"]     = False
        except Exception as e:
            print(f"[scanner] erreur: {e}")
        time.sleep(WATCH_INTERVAL_SECONDS)


def _serialize(m: MarketOpportunity) -> dict:
    osc = None
    if m.oscillation:
        osc = {
            "range_ticks": m.oscillation.range_ticks,
            "reversals":   m.oscillation.num_reversals,
            "score":       round(m.oscillation.score * 100),
        }
    shares = int(200 / m.bid) if m.bid > 0 else 0
    profit = round((m.ask - m.bid) * shares, 2) if m.bid > 0 else 0
    return {
        "question":    m.question,
        "slug":        m.slug,
        "volume_24h":  round(m.volume_24h),
        "bid":         round(m.bid * 100, 1),
        "ask":         round(m.ask * 100, 1),
        "spread":      round(m.spread_cents, 2),
        "bid_depth":   round(m.bid_depth),
        "ask_depth":   round(m.ask_depth),
        "score":       round(m.score),
        "shares":      shares,
        "profit":      profit,
        "end_date":    m.end_date[:10],
        "oscillation": osc,
        "url":         f"https://polymarket.com/event/{m.slug}",
    }


# ─── API ─────────────────────────────────────────────────────────────────────
@app.route("/api/markets")
def api_markets():
    with _lock:
        return jsonify(_cache)


# ─── HTML Dashboard ───────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polymarket Volume Scanner</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 13px;
  }

  header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border-bottom: 1px solid #30363d;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  header h1 {
    font-size: 16px;
    font-weight: 700;
    color: #58a6ff;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  #status {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: #8b949e;
  }

  #dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #3fb950;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
  }

  #countdown {
    color: #58a6ff;
    font-weight: 700;
    min-width: 28px;
    text-align: right;
  }

  main { padding: 20px 24px; max-width: 1400px; margin: 0 auto; }

  #loading {
    text-align: center;
    padding: 60px;
    color: #58a6ff;
    font-size: 14px;
  }

  .spinner {
    display: inline-block;
    width: 20px; height: 20px;
    border: 2px solid #30363d;
    border-top-color: #58a6ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 10px;
    vertical-align: middle;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
  }

  thead th {
    background: #161b22;
    padding: 10px 12px;
    text-align: left;
    color: #8b949e;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid #30363d;
    white-space: nowrap;
  }

  tbody tr {
    border-bottom: 1px solid #21262d;
    transition: background 0.15s;
    cursor: pointer;
  }

  tbody tr:hover { background: #161b22; }

  td {
    padding: 10px 12px;
    vertical-align: middle;
  }

  .rank { color: #8b949e; font-size: 11px; width: 28px; }

  .question {
    max-width: 320px;
    font-size: 12px;
    line-height: 1.4;
    color: #c9d1d9;
    font-weight: 500;
  }

  .question small {
    display: block;
    color: #8b949e;
    font-size: 10px;
    margin-top: 2px;
  }

  .price {
    color: #3fb950;
    font-weight: 700;
    font-size: 14px;
  }

  .spread-tight  { color: #3fb950; font-weight: 700; }
  .spread-ok     { color: #d29922; }
  .spread-wide   { color: #f85149; }

  .vol   { color: #58a6ff; }
  .depth { color: #8b949e; }

  .score-high { background: #1a4731; color: #3fb950; }
  .score-mid  { background: #2d2a0a; color: #d29922; }
  .score-low  { background: #21262d; color: #8b949e; }

  .score-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
  }

  .osc-good { color: #3fb950; font-weight: 700; }
  .osc-na   { color: #8b949e; }

  .action-btn {
    display: inline-block;
    background: #1f6feb;
    color: #fff;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    transition: background 0.15s;
  }

  .action-btn:hover { background: #388bfd; }

  .profit { color: #3fb950; font-size: 11px; }

  .best-pick {
    background: linear-gradient(135deg, #0d1117, #0f2a1d);
    border: 1px solid #3fb950;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }

  .best-pick-label {
    font-size: 11px;
    color: #3fb950;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }

  .best-pick-name {
    font-size: 14px;
    font-weight: 700;
    color: #fff;
  }

  .best-pick-detail {
    font-size: 12px;
    color: #8b949e;
    margin-top: 4px;
  }

  .tag {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 10px;
    margin-left: 4px;
  }

  .tag-ipl  { background: #1a3a5c; color: #58a6ff; }
  .tag-nba  { background: #2d1a3a; color: #bc8cff; }
  .tag-pol  { background: #1f2d1f; color: #56d364; }
  .tag-wc   { background: #1a2d3a; color: #79c0ff; }
</style>
</head>
<body>

<header>
  <h1>⚡ Polymarket Volume Scanner</h1>
  <div id="status">
    <div id="dot"></div>
    <span id="last-update">Chargement...</span>
    <span>· Refresh dans</span>
    <span id="countdown">60</span>s
  </div>
</header>

<main>
  <div id="loading">
    <span class="spinner"></span>
    Scan en cours — analyse des orderbooks...
  </div>
  <div id="best-pick-container"></div>
  <div id="table-container"></div>
</main>

<script>
let countdown = 60;
let timer;

function fmt_vol(v) {
  if (v >= 1000000) return '$' + (v/1000000).toFixed(1) + 'M';
  if (v >= 1000)    return '$' + (v/1000).toFixed(0) + 'k';
  return '$' + v;
}

function fmt_depth(d) {
  if (d >= 1000) return '$' + (d/1000).toFixed(1) + 'k';
  return '$' + d;
}

function spread_class(s) {
  if (s <= 0.1) return 'spread-tight';
  if (s <= 0.2) return 'spread-ok';
  return 'spread-wide';
}

function score_class(s) {
  if (s >= 70) return 'score-high';
  if (s >= 50) return 'score-mid';
  return 'score-low';
}

function category_tag(question) {
  const q = question.toLowerCase();
  if (q.includes('ipl') || q.includes('cricket')) return '<span class="tag tag-ipl">IPL</span>';
  if (q.includes('nba') || q.includes('spurs') || q.includes('lakers')) return '<span class="tag tag-nba">NBA</span>';
  if (q.includes('world cup') || q.includes('fifa')) return '<span class="tag tag-wc">WC26</span>';
  if (q.includes('2028') || q.includes('president') || q.includes('nomination')) return '<span class="tag tag-pol">POL</span>';
  return '';
}

function render(data) {
  document.getElementById('loading').style.display = 'none';
  document.getElementById('last-update').textContent = 'Mis à jour ' + data.last_update;

  const markets = data.markets;
  if (!markets || markets.length === 0) {
    document.getElementById('table-container').innerHTML = '<p style="color:#8b949e;padding:40px;text-align:center;">Aucun marché trouvé — scan en cours...</p>';
    return;
  }

  const best = markets[0];

  // Best pick banner
  document.getElementById('best-pick-container').innerHTML = `
    <div class="best-pick">
      <div>
        <div class="best-pick-label">⚡ Meilleur marché maintenant</div>
        <div class="best-pick-name">${best.question.substring(0,70)}${best.question.length>70?'...':''} ${category_tag(best.question)}</div>
        <div class="best-pick-detail">
          BUY LIMIT <b style="color:#3fb950">${best.bid}¢</b> &nbsp;→&nbsp;
          SELL <b style="color:#3fb950">${best.ask}¢</b> &nbsp;·&nbsp;
          ${best.shares} shares · $200 &nbsp;·&nbsp;
          Profit: <b style="color:#3fb950">+$${best.profit}</b>
        </div>
      </div>
      <a href="${best.url}" target="_blank" class="action-btn">Ouvrir sur Polymarket →</a>
    </div>`;

  // Table
  const rows = markets.map((m, i) => {
    const osc = m.oscillation
      ? `<span class="osc-good">${m.oscillation.range_ticks}¢ · ${m.oscillation.reversals}↕</span>`
      : `<span class="osc-na">—</span>`;

    const medals = ['🥇','🥈','🥉'];
    const rank = medals[i] || (i+1);

    return `
    <tr onclick="window.open('${m.url}','_blank')">
      <td class="rank">${rank}</td>
      <td class="question">
        ${m.question.substring(0,60)}${m.question.length>60?'...':''}
        ${category_tag(m.question)}
        <small>${m.end_date}</small>
      </td>
      <td class="vol">${fmt_vol(m.volume_24h)}</td>
      <td class="price">${m.bid}¢</td>
      <td class="price">${m.ask}¢</td>
      <td class="${spread_class(m.spread)}">${m.spread}¢</td>
      <td class="depth">${fmt_depth(m.bid_depth)}</td>
      <td>${osc}</td>
      <td><span class="score-badge ${score_class(m.score)}">${m.score}</span></td>
      <td>
        <div style="font-size:11px;color:#c9d1d9">${m.shares} shares</div>
        <div class="profit">+$${m.profit}</div>
      </td>
      <td><a href="${m.url}" target="_blank" class="action-btn" onclick="event.stopPropagation()">Trade →</a></td>
    </tr>`;
  }).join('');

  document.getElementById('table-container').innerHTML = `
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Marché</th>
          <th>Vol 24h</th>
          <th>Bid</th>
          <th>Ask</th>
          <th>Spread</th>
          <th>Depth bid</th>
          <th>Oscillation</th>
          <th>Score</th>
          <th>$200 → profit</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

async function fetchData() {
  try {
    const r = await fetch('/api/markets');
    const data = await r.json();
    if (!data.loading) render(data);
    else document.getElementById('last-update').textContent = 'Scan en cours...';
  } catch(e) {
    document.getElementById('last-update').textContent = 'Erreur réseau';
  }
}

function startCountdown() {
  clearInterval(timer);
  countdown = 60;
  timer = setInterval(() => {
    countdown--;
    document.getElementById('countdown').textContent = countdown;
    if (countdown <= 0) {
      countdown = 60;
      fetchData();
    }
  }, 1000);
}

// Init
fetchData();
startCountdown();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    # Lance le scanner en background
    t = threading.Thread(target=background_scan, daemon=True)
    t.start()

    print("\n  Polymarket Dashboard → http://localhost:8080")
    print("  Ctrl+C pour arrêter\n")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
