# ─── Polymarket Volume Scanner — Configuration ───────────────────────────────
import os

# Filtres marchés
MIN_VOLUME_24H   = 50_000   # $50k minimum (élargi pour plus de candidats)
MIN_PRICE        = 0.08     # 8¢ minimum
MAX_PRICE        = 0.92     # 92¢ maximum
MAX_SPREAD_CENTS = 1.0      # 1¢ spread maximum (élargi)

# Nombre de marchés à fetcher depuis l'API
FETCH_LIMIT = 300           # 300 marchés scannés (vs 100 avant)

# Capital par trade (pour calcul shares et profit)
TRADE_SIZE_USD = 200

# Refresh auto (--watch)
WATCH_INTERVAL_SECONDS = 60

# ─── Marchés à éviter (mots-clés, insensible à la casse) ─────────────────────
# Ajoute ici les marchés de tes bots pour ne pas se superposer
BOT_AVOID_KEYWORDS = [
    "iran",
    "kash patel",
    "tulsi",
    "iranian regime",
    "canada referendum",
    "fed rate",
    "interest rate",
    "federal reserve",
    "starmer",
    "ukraine ceasefire",
    "russia ukraine",
    "russia-ukraine",
    "wti crude",
    "china taiwan",
    "jesus christ",
    "gta vi",
    "gta6",
]

# ─── Base de données des top traders ─────────────────────────────────────────
# Chargée depuis whales.json (fichier local, non versionné sur GitHub)
# Pour configurer : cp whales.example.json whales.json  puis éditez-le
import json as _json

_whales_path = os.path.join(os.path.dirname(__file__), "whales.json")
if os.path.exists(_whales_path):
    with open(_whales_path, "r") as _f:
        WHALE_DATABASE = _json.load(_f)
else:
    WHALE_DATABASE = {}  # Aucun tracker configuré — voir whales.example.json

# Whales prioritaires à afficher dans le tracker (LEGENDARY + ELITE)
WHALE_WALLETS = {
    addr: info["name"]
    for addr, info in WHALE_DATABASE.items()
    if info["tier"] in ("LEGENDARY", "ELITE")
}

# Ton wallet (depuis .env → MY_WALLET=0x...)
MY_WALLET = os.getenv("MY_WALLET", "")

# ─── API endpoints ────────────────────────────────────────────────────────────
GAMMA_API  = "https://gamma-api.polymarket.com"
CLOB_API   = "https://clob.polymarket.com"
DATA_API   = "https://data-api.polymarket.com"
API_TIMEOUT = 15  # 15s pour les APIs lentes
