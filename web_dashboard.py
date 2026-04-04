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

from config import WATCH_INTERVAL_SECONDS, FETCH_LIMIT
from polymarket_scanner import (
    run_scanner, run_scanner_sport_du_jour, fetch_top_markets, MarketOpportunity,
    run_whale_tracker_api,
)

app = Flask(__name__)

# Cache global — mis à jour en background toutes les 60s
_cache = {"markets": [], "sport_du_jour": [], "whales": [], "last_update": None, "loading": True}
_lock  = threading.Lock()


# ─── Background scanner ───────────────────────────────────────────────────────
def background_scan():
    """Scan principal (Top Marchés) — rapide, ~30s."""
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


def background_scan_sport():
    """Scan sport (1500 marchés) — indépendant, ~2-3 min."""
    while True:
        try:
            sport = run_scanner_sport_du_jour()
            with _lock:
                _cache["sport_du_jour"] = sport
        except Exception as e:
            print(f"[sport] erreur: {e}")
        time.sleep(WATCH_INTERVAL_SECONDS * 3)  # refresh toutes les 3 min


def background_scan_whales():
    """Scan whales — indépendant."""
    while True:
        try:
            whales = run_whale_tracker_api()
            with _lock:
                _cache["whales"] = whales
        except Exception as e:
            print(f"[whales] erreur: {e}")
        time.sleep(WATCH_INTERVAL_SECONDS * 2)


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

@app.route("/api/markets/sport")
def api_sport():
    with _lock:
        return jsonify({"markets": _cache["sport_du_jour"], "last_update": _cache["last_update"]})


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

  /* ── Tabs ── */
  .tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 20px;
    border-bottom: 1px solid #21262d;
    padding-bottom: 0;
  }
  .tab {
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: #8b949e;
    cursor: pointer;
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 18px;
    letter-spacing: 0.5px;
    transition: color 0.15s, border-color 0.15s;
    margin-bottom: -1px;
  }
  .tab:hover { color: #c9d1d9; }
  .tab.active { color: #58a6ff; border-bottom-color: #1f6feb; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  /* ── 50/50 section ── */
  .section-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8b949e;
    margin: 0 0 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #21262d;
  }

  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 10px;
    margin-bottom: 28px;
  }

  .card-50 {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 14px;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
    position: relative;
    overflow: hidden;
  }
  .card-50:hover { border-color: #388bfd; background: #161b22; }

  .card-50.status-today  { border-color: #f85149; }
  .card-50.status-soon   { border-color: #d29922; }
  .card-50.status-upcoming { border-color: #21262d; }

  .card-50-bar {
    height: 3px;
    border-radius: 2px;
    margin-bottom: 10px;
    background: linear-gradient(to right, #1f6feb 0%, #3fb950 50%, #f85149 100%);
    position: relative;
  }
  .card-50-marker {
    position: absolute;
    top: -3px;
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #fff;
    border: 2px solid #0d1117;
    transform: translateX(-50%);
  }

  .card-50-question {
    font-size: 11px;
    color: #c9d1d9;
    line-height: 1.4;
    margin-bottom: 8px;
    font-weight: 500;
  }

  .card-50-prices {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .card-50-meta {
    font-size: 10px;
    color: #8b949e;
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
  }

  .status-badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .status-badge.today    { background: #3d1515; color: #f85149; }
  .status-badge.soon     { background: #2d2200; color: #d29922; }
  .status-badge.upcoming { background: #1a2d3a; color: #58a6ff; }

  .dist-badge {
    font-size: 10px;
    color: #3fb950;
    font-weight: 700;
  }

  .no-50-msg {
    color: #8b949e;
    font-size: 12px;
    padding: 20px;
    background: #0d1117;
    border: 1px dashed #21262d;
    border-radius: 8px;
    text-align: center;
    margin-bottom: 28px;
  }

  /* ── Filtres ── */
  .filter-bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px 14px;
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
  }
  .filter-bar label { font-size: 11px; color: #8b949e; white-space: nowrap; }
  .filter-bar select, .filter-bar input {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 5px;
    color: #c9d1d9;
    font-family: inherit;
    font-size: 11px;
    padding: 4px 8px;
    cursor: pointer;
  }
  .filter-bar select:hover, .filter-bar input:hover { border-color: #58a6ff; }
  .filter-count { font-size: 11px; color: #58a6ff; margin-left: auto; font-weight: 700; }

  /* ── Whale Tracker ── */
  .whale-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 10px;
    margin-bottom: 28px;
  }
  .whale-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 14px;
    transition: border-color 0.15s;
  }
  .whale-card:hover { border-color: #388bfd; }
  .whale-card.inactive { opacity: 0.45; }
  .whale-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  .whale-name { font-weight: 700; font-size: 13px; }
  .whale-tier-LEGENDARY { color: #bc8cff; }
  .whale-tier-ELITE     { color: #d29922; }
  .whale-tier-TOP       { color: #3fb950; }
  .whale-tier-HIGH      { color: #58a6ff; }
  .whale-tier-SOLID     { color: #79c0ff; }
  .whale-tier-VOLUME    { color: #8b949e; }
  .whale-badge {
    font-size: 9px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    background: #21262d;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .whale-wr { margin-left: auto; font-size: 11px; color: #3fb950; font-weight: 700; }
  .whale-market {
    font-size: 10px;
    color: #c9d1d9;
    padding: 3px 0;
    border-top: 1px solid #161b22;
    display: flex;
    justify-content: space-between;
    gap: 6px;
  }
  .whale-market-q { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .whale-market-meta { white-space: nowrap; color: #8b949e; }
  .whale-no-activity { font-size: 10px; color: #484f58; font-style: italic; }
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

  <nav class="tabs">
    <button class="tab active" data-tab="volume">📊 Top Marchés</button>
    <button class="tab" data-tab="sport">⚽ Sport du Jour</button>
    <button class="tab" data-tab="whales">🐋 Whale Tracker</button>
  </nav>

  <div id="tab-volume" class="tab-panel active">
    <div id="table-container"></div>
  </div>
  <div id="tab-sport" class="tab-panel">
    <div class="filter-bar">
      <label>Spread max</label>
      <select id="f-spread" onchange="applyFilters()">
        <option value="99">Tous</option>
        <option value="0.5">0.5¢</option>
        <option value="1" selected>1¢</option>
        <option value="2">2¢</option>
      </select>
      <label>Prix min</label>
      <select id="f-price" onchange="applyFilters()">
        <option value="0" selected>Tous</option>
        <option value="20">20¢+</option>
        <option value="30">30¢+</option>
        <option value="40">40¢+</option>
      </select>
      <label>Sport</label>
      <select id="f-sport" onchange="applyFilters()">
        <option value="">Tous</option>
        <option value="ufc">UFC/MMA</option>
        <option value="nba">NBA</option>
        <option value="nhl">NHL</option>
        <option value="mlb">MLB</option>
        <option value="nfl">NFL</option>
        <option value="soccer">Football</option>
        <option value="tennis">Tennis</option>
        <option value="cs2">CS2/LoL</option>
      </select>
      <span class="filter-count" id="sport-count"></span>
    </div>
    <div id="sport-container"></div>
  </div>
  <div id="tab-whales" class="tab-panel">
    <div id="whale-container"></div>
  </div>
</main>

<script>
let countdown = 60;
let timer;

// ── Tabs ──
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
  const name = t.dataset.tab;
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
}));

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

let _sportData = [];

const SPORT_MAP = {
  'ufc':    ['ufc','mma','fight night'],
  'nba':    ['nba'],
  'nhl':    ['nhl'],
  'mlb':    ['mlb'],
  'nfl':    ['nfl'],
  'soccer': ['premier league','champions league','ligue','bundesliga','serie a','la liga','balompié','will fc','will vf','will ss','will sc','will rc','will real','will club','will stade','o/u 2.5','o/u 3.5','both teams'],
  'tennis': ['tennis','open','wimbledon','masters','atp','wta'],
  'cs2':    ['counter-strike','cs2','lol:','league of legends','dota'],
};

function sportMatchesFilter(m) {
  const spread = parseFloat(document.getElementById('f-spread').value);
  const price  = parseFloat(document.getElementById('f-price').value);
  const sport  = document.getElementById('f-sport').value;
  const q      = m.question.toLowerCase();
  if (m.spread > spread) return false;
  if (m.bid < price) return false;
  if (sport) {
    const kws = SPORT_MAP[sport] || [sport];
    if (!kws.some(k => q.includes(k))) return false;
  }
  return true;
}

function sportIcon(q) {
  q = q.toLowerCase();
  if (q.includes('ufc') || q.includes('mma') || q.includes('fight night')) return '🥊';
  if (q.includes('nba') || q.includes('spurs') || q.includes('lakers') || q.includes('celtics') ||
      q.includes('heat') || q.includes('nuggets') || q.includes('wizards') || q.includes('warriors') ||
      q.includes('knicks') || q.includes('bulls') || q.includes('nets') || q.includes('bucks') ||
      q.includes('huskies') || q.includes('sooners') || q.includes('baylor') || q.includes('o/u 2') && q.includes('vs.') && !q.includes('goals')) return '🏀';
  if (q.includes('nhl') || q.includes('red wings') || q.includes('rangers') || q.includes('wild') ||
      q.includes('senators') || q.includes('avalanche') || q.includes('stars') || q.includes('flames') ||
      q.includes('ducks') || q.includes('penguins') || q.includes('bruins') || q.includes('leafs')) return '🏒';
  if (q.includes('mlb') || q.includes('cardinals') || q.includes('tigers') || q.includes('yankees') ||
      q.includes('red sox') || q.includes('dodgers') || q.includes('brewers') || q.includes('royals')) return '⚾';
  if (q.includes('nfl') || q.includes('chiefs') || q.includes('eagles') || q.includes('patriots')) return '🏈';
  if (q.includes('tennis') || q.includes('wimbledon') || q.includes('roland') || q.includes('atp') ||
      q.includes('wta') || q.includes('open') && q.includes('vs')) return '🎾';
  if (q.includes('counter-strike') || q.includes('cs2') || q.includes('lol:') || q.includes('dota') ||
      q.includes('league of legends') || q.includes('esport')) return '🎮';
  if (q.includes('formula') || q.includes('motogp') || q.includes('grand prix') || q.includes('f1')) return '🏎️';
  if (q.includes('ipl') || q.includes('cricket') || q.includes('rcb') || q.includes('csk')) return '🏏';
  // Football par défaut si on a des clubs connus
  return '⚽';
}

function makeCard(m) {
  const sc   = m.spread <= 0.5 ? '#3fb950' : m.spread <= 1 ? '#d29922' : '#f85149';
  const tc   = m.is_live
    ? (m.minutes_left < 60 ? '#f85149' : '#ff6b35')
    : (m.minutes_left < 360 ? '#d29922' : '#58a6ff');
  const icon = sportIcon(m.question);
  const badge = m.is_live
    ? `<span style="background:#3d0000;color:#f85149;border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">🔴 LIVE</span>`
    : '';
  return `
  <div class="card-50" onclick="window.open('${m.url}','_blank')">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <span style="display:flex;align-items:center;gap:6px">
        <span style="font-size:15px">${icon}</span>
        ${badge}
        <span style="color:${tc};font-weight:700;font-size:12px">⏱ ${m.time_left}</span>
      </span>
      <span style="color:#8b949e;font-size:10px">${fmt_vol(m.volume_24h)}</span>
    </div>
    <div class="card-50-question">
      ${m.question.substring(0,65)}${m.question.length>65?'...':''}
    </div>
    <div class="card-50-prices">
      <span style="color:#3fb950">${m.bid}¢</span>
      <span style="color:#8b949e;font-size:10px">bid</span>
      <span style="color:#8b949e">·</span>
      <span style="color:#58a6ff">${m.ask}¢</span>
      <span style="color:#8b949e;font-size:10px">ask</span>
      <span style="color:${sc};font-size:11px;margin-left:4px">${m.spread}¢ spread</span>
    </div>
    <div class="card-50-meta" style="margin-top:6px">
      <span style="color:#c9d1d9">${m.shares} shares · +$${m.profit}</span>
      <span style="color:#8b949e">${m.end_date}</span>
    </div>
  </div>`;
}

function sectionHtml(title, markets, emptyMsg) {
  if (!markets.length) return '';
  return `
    <div class="section-title">${title} <span style="color:#58a6ff;font-size:10px;margin-left:6px">${markets.length}</span></div>
    <div class="cards-grid" style="margin-bottom:24px">${markets.map(makeCard).join('')}</div>`;
}

function applyFilters() {
  const container = document.getElementById('sport-container');
  const filtered  = _sportData.filter(sportMatchesFilter);
  const live      = filtered.filter(m => m.is_live);
  const upcoming  = filtered.filter(m => !m.is_live);
  document.getElementById('sport-count').textContent = `${filtered.length} matchs`;

  if (!filtered.length) {
    container.innerHTML = '<div class="no-50-msg">Aucun match avec ces filtres.</div>';
    return;
  }
  container.innerHTML =
    sectionHtml('🔴 En cours / se termine bientôt', live) +
    sectionHtml('⏰ À venir aujourd\'hui', upcoming);
}

function renderSport(markets) {
  _sportData = markets || [];
  if (!_sportData.length) {
    document.getElementById('sport-container').innerHTML = `
      <div class="no-50-msg">Aucun match dans les 24 prochaines heures.<br>
      Les matchs IPL, NBA, UFC... apparaissent ici automatiquement le jour J.</div>`;
    document.getElementById('sport-count').textContent = '0 matchs';
    return;
  }
  applyFilters();
}

const TIER_ICONS = {
  LEGENDARY: '👑', ELITE: '🏆', TOP: '🥇', HIGH: '🥈', SOLID: '🥉', VOLUME: '📊'
};

function renderWhales(whales) {
  const container = document.getElementById('whale-container');
  if (!whales || !whales.length) {
    container.innerHTML = '<div class="no-50-msg">Aucune donnée whale disponible.</div>';
    return;
  }
  const cards = whales.map(w => {
    const icon    = TIER_ICONS[w.tier] || '•';
    const tierCls = 'whale-tier-' + w.tier;
    const inactive = w.active ? '' : ' inactive';
    const profileUrl = `https://polymarket.com/profile/${w.wallet}`;
    const mkts = w.markets.length
      ? w.markets.map(m => {
          const buyTag  = m.buys  ? `<span style="color:#3fb950;font-weight:700">${m.buys} achat${m.buys>1?'s':''}</span>` : '';
          const sellTag = m.sells ? `<span style="color:#f85149;font-weight:700">${m.sells} vente${m.sells>1?'s':''}</span>` : '';
          const sep = m.buys && m.sells ? ' · ' : '';
          return `
          <div class="whale-market">
            <span class="whale-market-q" title="${m.question}">${m.question}</span>
            <span class="whale-market-meta">${buyTag}${sep}${sellTag} · <span style="color:#c9d1d9">${m.avg_price}¢</span></span>
          </div>`;
        }).join('')
      : '<div class="whale-no-activity">Aucune activité récente</div>';
    return `
      <div class="whale-card${inactive}">
        <div class="whale-header">
          <span>${icon}</span>
          <a href="${profileUrl}" target="_blank" class="whale-name ${tierCls}" style="text-decoration:none">${w.name} ↗</a>
          <span class="whale-badge">${w.tier}</span>
          <span class="whale-wr">${w.win_rate}% WR</span>
        </div>
        ${mkts}
      </div>`;
  }).join('');
  container.innerHTML = `<div class="whale-grid">${cards}</div>`;
}

let _rendered = false;

function pollData() {
  fetch('/api/markets')
    .then(r => r.json())
    .then(data => {
      if (!data.loading) {
        try { render(data); } catch(e) { console.error('render error:', e); }
        try { renderSport(data.sport_du_jour); } catch(e) { console.error('sport error:', e); }
        try { renderWhales(data.whales); } catch(e) { console.error('whale error:', e); }
        if (!_rendered) { _rendered = true; startCountdown(); }
      }
    })
    .catch(e => console.error('fetch error:', e));
}

// Poll toutes les 2s jusqu'à affichage, puis toutes les 60s via startCountdown
setInterval(pollData, 2000);
pollData();
</script>
</body>
</html>"""


@app.route("/")
def index():
    from flask import make_response
    resp = make_response(HTML)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


if __name__ == "__main__":
    # Lance le scanner en background
    threading.Thread(target=background_scan,        daemon=True).start()
    threading.Thread(target=background_scan_sport,  daemon=True).start()
    threading.Thread(target=background_scan_whales, daemon=True).start()

    print("\n  Polymarket Dashboard → http://localhost:8080")
    print("  Ctrl+C pour arrêter\n")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
