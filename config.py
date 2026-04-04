# ─── Polymarket Volume Scanner — Configuration ───────────────────────────────

# Filtres marchés
MIN_VOLUME_24H = 100_000   # $100k minimum
MIN_PRICE      = 0.10      # 10¢ — en dessous trop extrême
MAX_PRICE      = 0.90      # 90¢ — au-dessus trop extrême
MAX_SPREAD_CENTS = 0.5     # 0.5¢ spread maximum

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
