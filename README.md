# ⚡ Polymarket Volume Scanner

> **Coach de trading manuel pour Polymarket** — Génère du volume leaderboard sans perdre d'argent.

![Dashboard Preview](https://img.shields.io/badge/Python-3.9+-blue) ![Flask](https://img.shields.io/badge/Flask-Web_Dashboard-green) ![Polymarket](https://img.shields.io/badge/Polymarket-CLOB-purple)

---

## 🎯 Stratégie

Achète à la limite BID (= MAKER = **0 fees**), revends au BID suivant (breakeven) ou à l'ASK (+profit).
**25 aller-retours × $400 = $10 000 de volume** avec ~$200 de capital.

```
BUY LIMIT  13.4¢  →  SELL LIMIT  13.5¢  →  profit : +$1.47 par round-trip
```

---

## 🚀 Installation

### 1. Clone le repo
```bash
git clone https://github.com/Gazettebale/polymarket-volume-scanner.git
cd polymarket-volume-scanner
```

### 2. Installe les dépendances
```bash
pip3 install requests flask
```

### 3. Configure ton wallet (optionnel)
```bash
cp .env.example .env
# Édite .env et mets ton adresse wallet Polymarket
```

### 4. Lance le dashboard web
```bash
python3 web_dashboard.py
```
Ouvre **http://localhost:8080** dans ton navigateur.

### 5. Ou lance le scanner terminal
```bash
python3 polymarket_scanner.py              # Scan complet
python3 polymarket_scanner.py --watch      # Refresh auto toutes les 60s
python3 polymarket_scanner.py --whale      # Whale tracker uniquement
python3 polymarket_scanner.py --top 10     # Top 10 marchés
```

---

## 📊 Dashboard Web

3 onglets :

| Onglet | Description |
|--------|-------------|
| 📊 **Top Marchés** | Meilleurs marchés pour générer du volume (spread serré, haut volume) |
| ⚽ **Sport du Jour** | Matchs en cours et à venir dans les 24h (UFC, NBA, foot, tennis...) |
| 🐋 **Whale Tracker** | Activité des 41 meilleurs traders Polymarket en temps réel |

---

## 🧠 Comment ça marche

### Scoring des marchés
Chaque marché reçoit un score sur 100 basé sur :
- **Spread** (35 pts) — plus le spread est serré, mieux c'est
- **Volume 24h** (25 pts) — plus de volume = plus de fills
- **Prix** (20 pts) — prix ni trop extrême ni trop central
- **Oscillation** (20 pts) — le marché bounce-t-il régulièrement ?

### 0 fees MAKER
Sur Polymarket CLOB, les ordres **LIMIT** (maker) ont **0% de frais**.
Les ordres market (taker) coûtent 0.5–1.8%.
→ On utilise **toujours des ordres limit** placés au BID ou à l'ASK.

### Whale Tracker
41 wallets de top traders (win rate 53%–100%) organisés par tier :
- 👑 LEGENDARY — 95%+ WR
- 🏆 ELITE — 85–95% WR
- 🥇 TOP — 80–85% WR
- 🥈 HIGH — 70–80% WR
- 🥉 SOLID — 60–70% WR
- 📊 VOLUME — gros volumes

---

## ⚙️ Configuration

Édite `config.py` pour ajuster :

```python
MIN_VOLUME_24H   = 50_000   # Volume minimum 24h
MAX_SPREAD_CENTS = 1.0      # Spread max en cents
TRADE_SIZE_USD   = 200      # Taille de chaque trade
FETCH_LIMIT      = 300      # Marchés scannés par run
```

---

## 📁 Structure

```
polymarket-volume-scanner/
├── polymarket_scanner.py   # Scanner principal + CLI
├── web_dashboard.py        # Dashboard Flask
├── config.py               # Configuration
├── .env.example            # Template variables d'env
└── README.md
```

---

## 🔗 APIs utilisées

| API | Usage |
|-----|-------|
| `gamma-api.polymarket.com` | Métadonnées marchés |
| `clob.polymarket.com` | Orderbook temps réel |
| `data-api.polymarket.com` | Activité wallets |

Toutes **publiques**, aucune clé API requise.

---

## ⚠️ Disclaimer

Cet outil est un **coach de trading manuel**. Il ne passe pas d'ordres automatiquement. Toutes les décisions de trading restent de ta responsabilité. Les marchés de prédiction comportent des risques.

---

Built by [@Gazettebale](https://x.com/Gazettebale) 🇫🇷
