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

# ─── Base de données des top traders ─────────────────────────────────────────
# Format: adresse → {name, win_rate, rank, tier}
# Tiers: LEGENDARY > ELITE > TOP > HIGH > SOLID > VOLUME
WHALE_DATABASE = {
    # 👑 LEGENDARY (95-100% WR)
    "0x4638d71d7b2d36eb590b5e1824955712dc8ad587": {"name": "jeb2016",       "win_rate": 100.0, "rank": 1590, "tier": "LEGENDARY"},
    "0x9b979a065641e8cfde3022a30ed2d9415cf55e12": {"name": "LlamaEnjoyer",  "win_rate": 96.0,  "rank": 69,   "tier": "LEGENDARY"},
    "0x7f3c8979d0afa00007bae4747d5347122af05613": {"name": "LucasMeow",     "win_rate": 95.5,  "rank": 411,  "tier": "LEGENDARY"},

    # 🏆 ELITE (85-95% WR)
    "0x2e0b70d482e6b389e81dea528be57d825dd48070": {"name": "Trump2028",            "win_rate": 92.2, "rank": 447,  "tier": "ELITE"},
    "0x6ffb4354cbe6e0f9989e3b55564ec5fb8646a834": {"name": "AgricultureSecretary", "win_rate": 91.7, "rank": 221,  "tier": "ELITE"},
    "0xa9b44dca52ed35e59ac2a6f49d1203b8155464ed": {"name": "VvVv",                 "win_rate": 90.4, "rank": 375,  "tier": "ELITE"},
    "0x8861f0bb5e0c19474ba73beeadc13ed8915beed6": {"name": "yjcr",                 "win_rate": 89.7, "rank": 60,   "tier": "ELITE"},
    "0xfc25f141ed27bb1787338d2c4e7f51e3a15e1f7f": {"name": "kutar",                "win_rate": 88.8, "rank": 274,  "tier": "ELITE"},
    "0xed107a85a4585a381e48c7f7ca4144909e7dd2e5": {"name": "bobe2",                "win_rate": 87.0, "rank": 52,   "tier": "ELITE"},
    "0x000d257d2dc7616feaef4ae0f14600fdf50a758e": {"name": "scottilicious",        "win_rate": 84.9, "rank": 44,   "tier": "ELITE"},

    # 🥇 TOP (80-85% WR)
    "0xcd71fd5370880f3d92bb941e628c05840fe0d127": {"name": "Kevindoto",    "win_rate": 81.5, "rank": 480, "tier": "TOP"},

    # 🥈 HIGH (70-80% WR)
    "0xa4b366ad22fc0d06f1e934ff468e8922431a87b8": {"name": "HolyMoses7",         "win_rate": 78.6, "rank": 789,  "tier": "HIGH"},
    "0x6bab41a0dc40d6dd4c1a915b8c01969479fd1292": {"name": "Dropper",            "win_rate": 78.4, "rank": 95,   "tier": "HIGH"},
    "0x220ce36c47fa467152b3bd8d431af74f232243c8": {"name": "numbersandletters",  "win_rate": 75.9, "rank": 384,  "tier": "HIGH"},
    "0xd218e474776403a330142299f7796e8ba32eb5c9": {"name": "BigVolume_d218",     "win_rate": 73.5, "rank": 107,  "tier": "HIGH"},
    "0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1": {"name": "aenews2",            "win_rate": 72.9, "rank": 22,   "tier": "HIGH"},
    "0x53d2d3c78597a78402d4db455a680da7ef560c3f": {"name": "abeautifulmind",     "win_rate": 72.5, "rank": 64,   "tier": "HIGH"},
    "0x83a296505eb520c9d35823571204ced41fd69452": {"name": "0x83a2_whale",       "win_rate": 72.2, "rank": 1543, "tier": "HIGH"},

    # 🥉 SOLID (60-70% WR)
    "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b": {"name": "Car",            "win_rate": 69.2, "rank": 106,  "tier": "SOLID"},
    "0x5bffcf561bcae83af680ad600cb99f1184d6ffbe": {"name": "YatSen",         "win_rate": 69.2, "rank": 19,   "tier": "SOLID"},
    "0xe3726a1b9c6ba2f06585d1c9e01d00afaedaeb38": {"name": "MegaVolume_e372","win_rate": 69.1, "rank": 324,  "tier": "SOLID"},
    "0xee00ba338c59557141789b127927a55f5cc5cea1": {"name": "S-Works",        "win_rate": 67.3, "rank": 24,   "tier": "SOLID"},
    "0x6770bf688b8121331b1c5cfd7723ebd4152545fb": {"name": "GreekGamblerPM", "win_rate": 65.6, "rank": 4834, "tier": "SOLID"},
    "0x24c8cf69a0e0a17eee21f69d29752bfa32e823e1": {"name": "debased",        "win_rate": 65.1, "rank": 46,   "tier": "SOLID"},
    "0x4b92a2d2fd3807981a5dddae7315122af05613":  {"name": "wisser",          "win_rate": 65.0, "rank": 406,  "tier": "SOLID"},
    "0x7ac83882979ccb5665cea83cb269e558b55077cd": {"name": "nicoco89",       "win_rate": 64.7, "rank": 1267, "tier": "SOLID"},
    "0xd1acd3925d895de9aec98ff95f3a30c5279d08d5": {"name": "Kickstand7",    "win_rate": 64.6, "rank": 45,   "tier": "SOLID"},
    "0x551e72eda42a5ab39d6d78239a1d9bbb5db6b0e0": {"name": "GayPride",      "win_rate": 64.3, "rank": 107,  "tier": "SOLID"},
    "0xdbade4c82fb72780a0db9a38f821d8671aba9c95": {"name": "SwissMiss",     "win_rate": 64.0, "rank": 16,   "tier": "SOLID"},
    "0x9d84ce0306f8551e02efef1680475fc0f1dc1344": {"name": "Domer",         "win_rate": 63.4, "rank": 19,   "tier": "SOLID"},
    "0xf2f6af4f27ec2dcf4072095ab804016e14cd5817": {"name": "gopfan2",       "win_rate": 63.0, "rank": 51,   "tier": "SOLID"},
    "0x509587cbb541251c74f261df3421f1fcc9fdc97c": {"name": "BuckMySalls",   "win_rate": 62.7, "rank": 67,   "tier": "SOLID"},
    "0x0f37cb80dee49d55b5f6d9e595d52591d6371410": {"name": "Hans323",       "win_rate": 61.7, "rank": 904,  "tier": "SOLID"},
    "0x06ecb7e739f5455922ce57e83284f132c7f0f845": {"name": "frosen",        "win_rate": 60.8, "rank": 434,  "tier": "SOLID"},

    # 📊 VOLUME (traders à fort volume)
    "0xb74711992caf6d04fa55eecc46b8efc95311b050": {"name": "Kapii",              "win_rate": 59.5, "rank": 63,  "tier": "VOLUME"},
    "0x629bc4a1e53e1d475beb7ea3d388791e96dd995a": {"name": "lava-lava",          "win_rate": 58.9, "rank": 172, "tier": "VOLUME"},
    "0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3": {"name": "coinman2",           "win_rate": 57.3, "rank": 53,  "tier": "VOLUME"},
    "0x8795bcb2fe129d1ea3e3d73bc13a3d8078047544": {"name": "ciro2",             "win_rate": 57.2, "rank": 93,  "tier": "VOLUME"},
    "0x39932ca2b7a1b8ab6cbf0b8f7419261b950ccded": {"name": "kIjsa12345",        "win_rate": 53.8, "rank": 255, "tier": "VOLUME"},
    "0x889e7f0464c72eb8cda1525ebc12b6aaba9d09e0": {"name": "Punchbowl",         "win_rate": 53.6, "rank": 90,  "tier": "VOLUME"},
    "0x31519628fb5e5aa559d4ba27aa1248810b9f0977": {"name": "qwertyasdfghjkl",   "win_rate": 53.3, "rank": 35,  "tier": "VOLUME"},
}

# Whales prioritaires à afficher dans le tracker (LEGENDARY + ELITE)
WHALE_WALLETS = {
    addr: info["name"]
    for addr, info in WHALE_DATABASE.items()
    if info["tier"] in ("LEGENDARY", "ELITE")
}

# Ton wallet (pour exclure tes propres marchés actifs)
MY_WALLET = "0xCB46AffadF07F3deBc1dCEf56b57108cbF793692"

# ─── API endpoints ────────────────────────────────────────────────────────────
GAMMA_API  = "https://gamma-api.polymarket.com"
CLOB_API   = "https://clob.polymarket.com"
DATA_API   = "https://data-api.polymarket.com"
API_TIMEOUT = 8
