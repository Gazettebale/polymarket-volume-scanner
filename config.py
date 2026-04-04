# ─── Polymarket Volume Scanner — Configuration ───────────────────────────────

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

# ─── Whales à suivre ─────────────────────────────────────────────────────────
# Remplis les adresses Polygon depuis polymarket.com/@username
# → Ouvre le profil → clique sur une transaction → copie l'adresse Polygon
WHALE_WALLETS = {
    "sovereign2013":        "",   # $361M vol, +$1.7M profit
    "RN1":                  "",   # $351M vol, +$1.6M profit
    "GamblingIsAllYouNeed": "",   # $306M vol
}

# Ton wallet (pour exclure tes propres marchés actifs)
MY_WALLET = "0xCB46AffadF07F3deBc1dCEf56b57108cbF793692"

# ─── API endpoints ────────────────────────────────────────────────────────────
GAMMA_API  = "https://gamma-api.polymarket.com"
CLOB_API   = "https://clob.polymarket.com"
DATA_API   = "https://data-api.polymarket.com"
API_TIMEOUT = 8
