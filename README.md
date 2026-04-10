# ⚡ Polymarket Volume Scanner

> **Manual trading coach for Polymarket** — Volume scanner, whale tracker, sport markets & CLOB leaderboard in one dashboard.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Flask](https://img.shields.io/badge/Flask-Web_Dashboard-green) ![Polymarket](https://img.shields.io/badge/Polymarket-CLOB-purple)

---

## 🎯 Strategy

Buy at the BID limit (= MAKER = **0 fees**), sell at the next BID (breakeven) or at the ASK (+profit).
**25 round-trips × $400 = $10,000 in volume** with ~$200 capital.

```
BUY LIMIT  13.4¢  →  SELL LIMIT  13.5¢  →  profit: +$1.47 per round-trip
```

---

## 🚀 Installation

### 1. Clone the repo
```bash
git clone https://github.com/Gazettebale/polymarket-volume-scanner.git
cd polymarket-volume-scanner
```

### 2. Install dependencies
```bash
pip3 install requests flask flask-socketio
```

### 3. Launch the web dashboard
```bash
python3 web_dashboard.py
```
Open **http://localhost:8080** in your browser.

### 4. Or run the terminal scanner
```bash
python3 polymarket_scanner.py              # Full scan
python3 polymarket_scanner.py --watch      # Auto-refresh every 60s
python3 polymarket_scanner.py --whale      # Whale tracker only
python3 polymarket_scanner.py --top 10     # Show top 10 markets
```

---

## 📊 Web Dashboard

4 tabs:

| Tab | Description |
|-----|-------------|
| 📊 **Top Markets** | Best markets for volume generation (tight spread, high volume) |
| ⚽ **Sport of the Day** | Live & upcoming matches in the next 24h (UFC, NBA, soccer, tennis...) |
| 🐋 **Whale Tracker** | Real-time activity of 41 top Polymarket traders |
| 🏆 **Leaderboard CLOB** | Full CLOB API leaderboard — find your real rank by proxy wallet |

---

## 🏆 Leaderboard CLOB

The official Polymarket leaderboard only tracks browser-wallet users. If you trade via the **CLOB API** (market making, bots, reward farming), your real stats live on a **proxy wallet**.

Features:
- **Full leaderboard** — top traders sorted by P&L or Volume, all time / monthly / weekly / daily
- **Rank Finder** — paste your proxy wallet to see your true P&L, volume, return on volume
- **Rank estimation** — log-log interpolation gives your estimated rank even outside top 50
- **Activity stats** — first trade date, fill count, avg fill size, last 10 fills
- **Share link** — copy a direct URL to any wallet's stats

All data fetched client-side from `lb-api.polymarket.com` — no server changes needed.

---

## 🧠 How it works

### Market Scoring
Each market gets a score out of 100 based on:
- **Spread** (35 pts) — the tighter the spread, the better
- **24h Volume** (25 pts) — more volume = faster fills
- **Price** (20 pts) — not too extreme, not too central
- **Oscillation** (20 pts) — does the market bounce regularly?

### 0 Fee MAKER Orders
On Polymarket CLOB, **LIMIT orders** (maker) have **0% fees**.
Market orders (taker) cost 0.5–1.8%.
→ Always use **limit orders** placed at the BID or ASK.

### Whale Tracker
41 top trader wallets (53%–100% win rate) organized by tier:
- 👑 LEGENDARY — 95%+ WR
- 🏆 ELITE — 85–95% WR
- 🥇 TOP — 80–85% WR
- 🥈 HIGH — 70–80% WR
- 🥉 SOLID — 60–70% WR
- 📊 VOLUME — high volume traders

---

## ⚙️ Configuration

Edit `config.py` to adjust:

```python
MIN_VOLUME_24H   = 50_000   # Minimum 24h volume
MAX_SPREAD_CENTS = 1.0      # Max spread in cents
TRADE_SIZE_USD   = 200      # Size per trade
FETCH_LIMIT      = 300      # Markets scanned per run
```

---

## 📁 Structure

```
polymarket-volume-scanner/
├── polymarket_scanner.py   # Core scanner + CLI
├── web_dashboard.py        # Flask dashboard (all 4 tabs)
├── config.py               # Configuration
├── requirements.txt        # Dependencies
└── README.md
```

---

## 🔗 APIs Used

| API | Usage |
|-----|-------|
| `gamma-api.polymarket.com` | Market metadata |
| `clob.polymarket.com` | Real-time orderbook |
| `data-api.polymarket.com` | Wallet activity & fills |
| `lb-api.polymarket.com` | CLOB leaderboard (P&L, volume, rank) |

All **public APIs** — no API key required.

---

## ⚠️ Disclaimer

This tool is a **manual trading coach**. It does not place orders automatically. All trading decisions remain your responsibility. Prediction markets involve risk.

---

Built by [@Gazettebale](https://x.com/Gazettebale) 🇫🇷
