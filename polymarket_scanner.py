#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        POLYMARKET VOLUME SCANNER — Gazettebale               ║
║  Trouve les marchés idéaux pour générer du volume            ║
║  sans perdre d'argent                                        ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python3 polymarket_scanner.py              → scan complet
  python3 polymarket_scanner.py --whale      → whale tracker uniquement
  python3 polymarket_scanner.py --watch      → refresh auto toutes les 60s
  python3 polymarket_scanner.py --top 10     → top N marchés
"""

import sys
import time
import json
import argparse
import requests
import json as _json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

# ─── ANSI Colors ────────────────────────────────────────────────────────────
R  = "\033[0m"       # Reset
B  = "\033[1m"       # Bold
G  = "\033[92m"      # Green
Y  = "\033[93m"      # Yellow
RE = "\033[91m"      # Red
CY = "\033[96m"      # Cyan
MA = "\033[95m"      # Magenta
DG = "\033[90m"      # Dark gray
BG = "\033[42m"      # Green background
BY = "\033[43m"      # Yellow background

# ─── Config (depuis config.py) ───────────────────────────────────────────────
from config import (
    GAMMA_API, CLOB_API, DATA_API,
    MIN_VOLUME_24H as MIN_VOLUME,
    MIN_PRICE, MAX_PRICE,
    MAX_SPREAD_CENTS as MAX_SPREAD,
    TRADE_SIZE_USD,
    WATCH_INTERVAL_SECONDS,
    FETCH_LIMIT,
    BOT_AVOID_KEYWORDS,
    WHALE_WALLETS,
    WHALE_DATABASE,
    MY_WALLET,
    API_TIMEOUT as TIMEOUT,
)


# ─── Data classes ────────────────────────────────────────────────────────────
@dataclass
class OscillationData:
    range_ticks: float      # amplitude en cents (0.1¢ = 1 tick)
    num_reversals: int      # nombre de fois où la direction change
    recent_prices: list     # liste des derniers prix
    avg_price: float        # prix moyen récent
    score: float            # 0.0 → 1.0 (1.0 = oscillation parfaite)

@dataclass
class MarketOpportunity:
    question: str
    slug: str
    token_id_yes: str
    token_id_no: str
    volume_24h: float
    yes_price: float        # prix gamma API (approx mid)
    end_date: str

    # Orderbook réel
    bid: float = 0.0
    ask: float = 0.0
    spread_cents: float = 0.0
    bid_depth: float = 0.0  # $ disponibles au bid
    ask_depth: float = 0.0

    # Oscillation
    oscillation: Optional[OscillationData] = None

    # Score final
    score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)


# ─── API calls ───────────────────────────────────────────────────────────────
def fetch_top_markets(limit: int = 300) -> list:
    """
    Récupère les marchés avec le plus de volume 24h.
    Pagine automatiquement si limit > 300 (max API par appel).
    """
    all_markets = []
    page_size   = 300
    offset      = 0
    remaining   = limit

    while remaining > 0:
        batch = min(page_size, remaining)
        try:
            r = requests.get(
                f"{GAMMA_API}/markets",
                params={
                    "active":    "true",
                    "closed":    "false",
                    "limit":     batch,
                    "offset":    offset,
                    "order":     "volume24hr",
                    "ascending": "false",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            all_markets.extend(data)
            if len(data) < batch:   # dernière page
                break
            offset    += batch
            remaining -= batch
        except Exception as e:
            print(f"{RE}[ERROR] fetch_top_markets page {offset}: {e}{R}")
            break

    return all_markets


def fetch_orderbook(token_id: str) -> Optional[dict]:
    """Récupère le vrai orderbook CLOB (bid/ask/depth)."""
    try:
        r = requests.get(
            f"{CLOB_API}/book",
            params={"token_id": token_id},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        bids = sorted(data.get("bids", []), key=lambda x: float(x["price"]), reverse=True)
        asks = sorted(data.get("asks", []), key=lambda x: float(x["price"]))

        if not bids or not asks:
            return None

        best_bid = float(bids[0]["price"])
        best_ask = float(asks[0]["price"])
        spread = round((best_ask - best_bid) * 100, 2)  # en cents

        # Depth: somme $ des 3 premiers niveaux
        bid_depth = sum(float(b["price"]) * float(b["size"]) for b in bids[:3])
        ask_depth = sum(float(a["price"]) * float(a["size"]) for a in asks[:3])

        return {
            "bid": best_bid,
            "ask": best_ask,
            "spread_cents": spread,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "bids": bids[:5],
            "asks": asks[:5],
        }
    except Exception:
        return None


def fetch_recent_trades(token_id: str, limit: int = 100) -> list:
    """Récupère les derniers trades pour analyser l'oscillation."""
    try:
        r = requests.get(
            f"{CLOB_API}/trades",
            params={"token_id": token_id, "limit": limit},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def fetch_user_activity(wallet: str, limit: int = 30) -> list:
    """Récupère l'activité récente d'un wallet (whale tracking)."""
    try:
        r = requests.get(
            f"{DATA_API}/activity",
            params={"user": wallet, "limit": limit},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


# ─── Analysis ────────────────────────────────────────────────────────────────
def is_on_avoid_list(question: str) -> bool:
    """Vérifie si le marché est sur la liste d'évitement des bots."""
    q = question.lower()
    return any(kw in q for kw in BOT_AVOID_KEYWORDS)


def is_expired_or_today(end_date: str) -> bool:
    """Filtre les marchés déjà expirés ET ceux qui résolvent aujourd'hui."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        end = end_date[:10]  # YYYY-MM-DD
        return end <= today   # exclut passé + aujourd'hui
    except Exception:
        return False


def analyze_oscillation(trades: list) -> Optional[OscillationData]:
    """
    Détecte si un marché oscille dans un range de 2-3 ticks.

    Idéal pour le volume: prix qui monte et descend en boucle
    dans un range < 3 ticks → on achète au bid, on vend au ask, repeat.
    """
    if len(trades) < 15:
        return None

    try:
        prices = [float(t["price"]) for t in trades[:50] if "price" in t]
        if len(prices) < 10:
            return None

        recent = prices[:30]
        range_price = max(recent) - min(recent)
        range_ticks = round(range_price * 100, 2)  # en cents
        avg_price = sum(recent) / len(recent)

        # Compter les reversals (changements de direction)
        reversals = 0
        for i in range(2, len(recent)):
            up_then_down = recent[i] < recent[i-1] and recent[i-1] >= recent[i-2]
            down_then_up = recent[i] > recent[i-1] and recent[i-1] <= recent[i-2]
            if up_then_down or down_then_up:
                reversals += 1

        # Score oscillation:
        # Range 0-1¢ + beaucoup de reversals = parfait
        # Range 1-3¢ + reversals = bien
        # Range > 3¢ = mauvais pour la stratégie
        if range_ticks <= 0.5:
            range_score = 1.0
        elif range_ticks <= 1.0:
            range_score = 0.9
        elif range_ticks <= 2.0:
            range_score = 0.7
        elif range_ticks <= 3.0:
            range_score = 0.4
        else:
            range_score = 0.0

        reversal_score = min(reversals / 12, 1.0)  # 12+ reversals = score max
        osc_score = range_score * 0.6 + reversal_score * 0.4

        return OscillationData(
            range_ticks=range_ticks,
            num_reversals=reversals,
            recent_prices=recent[:10],
            avg_price=avg_price,
            score=round(osc_score, 3),
        )
    except Exception:
        return None


def score_market(m: MarketOpportunity) -> float:
    """
    Score global de suitabilité pour la stratégie de volume.

    Critères:
    - Spread serré (0 fees, sortie facile)
    - Volume élevé (fills rapides)
    - Prix dans la zone sûre (20-80¢)
    - Oscillation dans 2-3 ticks (round trips faciles)
    - Depth suffisante (peut absorber $200)
    """
    breakdown = {}

    # 1. Score spread (35 pts max)
    if m.spread_cents <= 0.1:
        s_spread = 35
    elif m.spread_cents <= 0.2:
        s_spread = 30
    elif m.spread_cents <= 0.5:
        s_spread = 20
    elif m.spread_cents <= 1.0:
        s_spread = 10
    else:
        s_spread = 0
    breakdown["spread"] = s_spread

    # 2. Score volume (25 pts max)
    if m.volume_24h >= 1_000_000:
        s_vol = 25
    elif m.volume_24h >= 500_000:
        s_vol = 20
    elif m.volume_24h >= 200_000:
        s_vol = 15
    elif m.volume_24h >= 100_000:
        s_vol = 8
    else:
        s_vol = 0
    breakdown["volume"] = s_vol

    # 3. Score prix (20 pts max) — le milieu (40-60¢) est idéal
    price = m.bid if m.bid > 0 else m.yes_price
    dist_from_mid = abs(price - 0.5)
    if dist_from_mid <= 0.10:   # 40-60¢
        s_price = 20
    elif dist_from_mid <= 0.20: # 30-70¢
        s_price = 15
    elif dist_from_mid <= 0.30: # 20-80¢
        s_price = 10
    else:
        s_price = 5
    breakdown["price"] = s_price

    # 4. Score oscillation (20 pts max)
    if m.oscillation:
        s_osc = round(m.oscillation.score * 20)
    else:
        s_osc = 0
    breakdown["oscillation"] = s_osc

    total = s_spread + s_vol + s_price + s_osc
    m.score_breakdown = breakdown
    return float(total)


# ─── Display ─────────────────────────────────────────────────────────────────
def fmt_price(p: float) -> str:
    return f"{p*100:.1f}¢"


def fmt_volume(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}k"
    return f"${v:.0f}"


def fmt_spread(s: float) -> str:
    if s <= 0.1:
        return f"{G}{B}{s}¢{R}"
    if s <= 0.2:
        return f"{G}{s}¢{R}"
    if s <= 0.5:
        return f"{Y}{s}¢{R}"
    return f"{RE}{s}¢{R}"


def fmt_score(s: float) -> str:
    if s >= 75:
        return f"{BG}{B} {s:.0f}/100 {R}"
    if s >= 55:
        return f"{G}{B}{s:.0f}/100{R}"
    if s >= 35:
        return f"{Y}{s:.0f}/100{R}"
    return f"{DG}{s:.0f}/100{R}"


def fmt_oscillation(osc: Optional[OscillationData]) -> str:
    if osc is None:
        return f"{DG}N/A{R}"
    if osc.range_ticks <= 1.0 and osc.num_reversals >= 8:
        tag = f"{G}{B}IDEAL{R}"
    elif osc.range_ticks <= 2.0 and osc.num_reversals >= 5:
        tag = f"{G}BON{R}"
    elif osc.range_ticks <= 3.0:
        tag = f"{Y}OK{R}"
    else:
        tag = f"{DG}TROP LARGE{R}"
    return f"{tag} {DG}({osc.range_ticks:.1f}¢ range, {osc.num_reversals} reversals){R}"


def print_header():
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{CY}{B}{'═'*70}{R}")
    print(f"{CY}{B}  POLYMARKET VOLUME SCANNER   {DG}{now}{R}")
    print(f"{CY}{B}{'═'*70}{R}\n")


def print_market_card(rank: int, m: MarketOpportunity):
    """Affiche une carte détaillée pour un marché."""

    # En-tête
    medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f" {rank}."
    print(f"\n{B}{medal}  {m.question[:65]}{R}")
    print(f"   {DG}{m.end_date[:10]}  ·  {fmt_volume(m.volume_24h)}/24h{R}")

    # Prix et spread
    if m.bid > 0:
        osc_range = f"  [{fmt_price(m.oscillation.avg_price - m.oscillation.range_ticks/200):.0f}–{fmt_price(m.oscillation.avg_price + m.oscillation.range_ticks/200):.0f}]" if m.oscillation else ""
        print(f"   {B}BID{R} {G}{fmt_price(m.bid)}{R}  {B}ASK{R} {G}{fmt_price(m.ask)}{R}  "
              f"Spread: {fmt_spread(m.spread_cents)}"
              f"{DG}{osc_range}{R}")

        # Depth
        print(f"   Depth bid: {G}${m.bid_depth:,.0f}{R}  ask: {G}${m.ask_depth:,.0f}{R}")

    # Oscillation
    print(f"   Oscillation: {fmt_oscillation(m.oscillation)}")

    # Score breakdown
    bd = m.score_breakdown
    print(f"   Score: {fmt_score(m.score)}  "
          f"{DG}[spread:{bd.get('spread',0)} vol:{bd.get('volume',0)} "
          f"prix:{bd.get('price',0)} osc:{bd.get('oscillation',0)}]{R}")

    # Instruction de trade
    if m.bid > 0:
        shares_200 = int(TRADE_SIZE_USD / m.bid)
        profit_1tick = round((m.ask - m.bid) * shares_200, 2)
        print(f"   {CY}→ BUY LIMIT {fmt_price(m.bid)} · {shares_200} shares · ${TRADE_SIZE_USD}{R}  "
              f"{G}Profit si ask: +${profit_1tick:.2f}{R}")

    print(f"   {DG}slug: {m.slug}{R}")


def print_summary_table(opportunities: list):
    """Tableau récapitulatif rapide."""
    print(f"\n{B}{'─'*70}{R}")
    print(f"{B}{'#':<3} {'Marché':<35} {'Vol':<8} {'Spread':<8} {'Osc':<6} {'Score'}{R}")
    print(f"{'─'*70}")

    for i, m in enumerate(opportunities, 1):
        q = m.question[:33] + ".." if len(m.question) > 35 else m.question.ljust(35)
        osc_tag = "✓" if (m.oscillation and m.oscillation.range_ticks <= 2.0) else "·"
        print(f"{i:<3} {q:<35} {fmt_volume(m.volume_24h):<8} "
              f"{m.spread_cents:.1f}¢     {osc_tag}      {m.score:.0f}")


# ─── Whale Tracker ───────────────────────────────────────────────────────────
TIER_COLORS = {
    "LEGENDARY": MA + B,
    "ELITE":     Y  + B,
    "TOP":       G  + B,
    "HIGH":      CY + B,
    "SOLID":     "\033[94m" + B,  # Blue
    "VOLUME":    DG,
}
TIER_ICONS = {
    "LEGENDARY": "👑",
    "ELITE":     "🏆",
    "TOP":       "🥇",
    "HIGH":      "🥈",
    "SOLID":     "🥉",
    "VOLUME":    "📊",
}


def get_whale_activity(wallet: str, limit: int = 30) -> list:
    """Récupère l'activité récente d'un wallet via data-api."""
    try:
        r = requests.get(
            f"{DATA_API}/activity",
            params={"user": wallet, "limit": limit},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        if isinstance(data, list):
            return data
        return data.get("data", []) or data.get("activity", [])
    except Exception:
        return []


def run_whale_tracker_api() -> list:
    """
    Retourne une liste de dicts pour le dashboard web :
    [{name, tier, win_rate, rank, wallet, markets: [{question, side, price, count}]}]
    """
    results = []
    for wallet, info in WHALE_DATABASE.items():
        activity = get_whale_activity(wallet, limit=30)
        market_agg = {}
        for tx in activity:
            question = (tx.get("title") or tx.get("market") or
                        tx.get("question") or tx.get("conditionId", "?"))[:55]
            side  = str(tx.get("side", "")).lower()
            price = float(tx.get("price") or tx.get("usdcSize") or 0)
            if question not in market_agg:
                market_agg[question] = {"buys": 0, "sells": 0, "prices": []}
            if "buy" in side:
                market_agg[question]["buys"] += 1
            else:
                market_agg[question]["sells"] += 1
            market_agg[question]["prices"].append(price)

        top_markets = []
        for q, d in list(market_agg.items())[:4]:
            avg_p = sum(d["prices"]) / len(d["prices"]) if d["prices"] else 0
            top_markets.append({
                "question": q,
                "buys":     d["buys"],
                "sells":    d["sells"],
                "avg_price": round(avg_p * 100, 1),
            })

        results.append({
            "name":     info["name"],
            "tier":     info["tier"],
            "win_rate": info["win_rate"],
            "rank":     info["rank"],
            "wallet":   wallet,
            "active":   len(market_agg) > 0,
            "markets":  top_markets,
        })

    # Trier : actifs d'abord, puis par tier puis win_rate
    tier_order = ["LEGENDARY", "ELITE", "TOP", "HIGH", "SOLID", "VOLUME"]
    results.sort(key=lambda x: (
        0 if x["active"] else 1,
        tier_order.index(x["tier"]) if x["tier"] in tier_order else 99,
        -x["win_rate"],
    ))
    return results


def run_whale_tracker():
    """Affiche l'activité récente des gros traders (terminal)."""
    print(f"\n{MA}{B}{'═'*60}{R}")
    print(f"{MA}{B}  WHALE TRACKER — {len(WHALE_DATABASE)} wallets surveillés{R}")
    print(f"{MA}{B}{'═'*60}{R}\n")

    shown = 0
    for wallet, info in WHALE_DATABASE.items():
        tier   = info["tier"]
        name   = info["name"]
        wr     = info["win_rate"]
        icon   = TIER_ICONS.get(tier, "•")
        color  = TIER_COLORS.get(tier, "")

        activity = get_whale_activity(wallet, limit=20)
        if not activity:
            continue

        shown += 1
        print(f"  {icon} {color}{name}{R} {DG}({tier} • {wr}% WR){R}")

        market_counts: dict = {}
        for tx in activity:
            q     = (tx.get("title") or tx.get("market") or
                     tx.get("question") or "?")[:50]
            side  = str(tx.get("side", "")).lower()
            price = float(tx.get("price") or 0)
            if q not in market_counts:
                market_counts[q] = {"buys": 0, "sells": 0, "prices": []}
            if "buy" in side:
                market_counts[q]["buys"] += 1
            else:
                market_counts[q]["sells"] += 1
            market_counts[q]["prices"].append(price)

        for market, data in list(market_counts.items())[:3]:
            avg_p = sum(data["prices"]) / len(data["prices"]) if data["prices"] else 0
            b_tag = f"{G}{data['buys']}B{R}" if data["buys"] else ""
            s_tag = f"{RE}{data['sells']}S{R}" if data["sells"] else ""
            print(f"    {CY}{market}{R}")
            print(f"    {b_tag} {s_tag}  moy {avg_p*100:.1f}¢")
        print()

    if shown == 0:
        print(f"  {DG}Aucune activité récente détectée (API lente ou wallets inactifs){R}\n")


# ─── Main Scanner ────────────────────────────────────────────────────────────
def run_scanner(top_n: int = 15, verbose: bool = True) -> list:
    """
    Scan principal: récupère, filtre, analyse et score tous les marchés.
    Retourne la liste triée des meilleures opportunités.
    """
    print(f"\n{CY}Fetching top marchés...{R}", end="", flush=True)
    raw_markets = fetch_top_markets(limit=FETCH_LIMIT)
    print(f" {G}{len(raw_markets)} marchés récupérés{R}")

    candidates = []
    skipped = {"bot_avoid": 0, "extreme_price": 0, "today": 0, "low_volume": 0, "no_tokens": 0}

    print(f"{CY}Filtrage...{R}")
    for m in raw_markets:
        q = m.get("question", "")
        vol = float(m.get("volume24hr") or 0)
        end = m.get("endDate", "") or m.get("end_date", "")
        tokens = m.get("clobTokenIds") or m.get("tokens", [])
        if isinstance(tokens, str):
            try:
                tokens = _json.loads(tokens)
            except Exception:
                tokens = []
        outcome_prices = m.get("outcomePrices", [])

        # Filtres rapides
        if vol < MIN_VOLUME:
            skipped["low_volume"] += 1
            continue
        if is_on_avoid_list(q):
            skipped["bot_avoid"] += 1
            continue
        if is_expired_or_today(end):
            skipped["today"] += 1
            continue
        if not tokens or len(tokens) < 2:
            skipped["no_tokens"] += 1
            continue

        # Prix YES approximatif (outcomePrices peut être une string JSON)
        try:
            if isinstance(outcome_prices, str):
                outcome_prices = _json.loads(outcome_prices)
            yes_price = float(outcome_prices[0]) if outcome_prices else 0.5
        except Exception:
            yes_price = 0.5

        if yes_price < MIN_PRICE or yes_price > MAX_PRICE:
            skipped["extreme_price"] += 1
            continue

        # Extraire token IDs
        if isinstance(tokens[0], dict):
            token_id_yes = tokens[0].get("token_id", tokens[0].get("id", ""))
            token_id_no  = tokens[1].get("token_id", tokens[1].get("id", "")) if len(tokens) > 1 else ""
        else:
            token_id_yes = str(tokens[0])
            token_id_no  = str(tokens[1]) if len(tokens) > 1 else ""

        # URL slug : utiliser le slug de l'event parent si dispo (évite les 404)
        events = m.get("events", [])
        event_slug = events[0].get("slug", "") if events else ""
        url_slug = event_slug or m.get("slug", "")

        candidates.append(MarketOpportunity(
            question=q,
            slug=url_slug,
            token_id_yes=token_id_yes,
            token_id_no=token_id_no,
            volume_24h=vol,
            yes_price=yes_price,
            end_date=end,
        ))

    print(f"  {G}{len(candidates)} candidats{R} après filtres  "
          f"{DG}(bot:{skipped['bot_avoid']} extreme:{skipped['extreme_price']} "
          f"today:{skipped['today']} vol:{skipped['low_volume']}){R}")

    # Analyse approfondie des candidats (orderbook + oscillation)
    print(f"\n{CY}Analyse orderbook + oscillation pour {len(candidates)} marchés...{R}\n")

    analyzed = []
    for i, m in enumerate(candidates):
        if not m.token_id_yes:
            continue

        sys.stdout.write(f"\r  [{i+1}/{len(candidates)}] {m.question[:50]:<50}")
        sys.stdout.flush()

        # Orderbook
        ob = fetch_orderbook(m.token_id_yes)
        if ob and ob["bid"] >= MIN_PRICE and ob["ask"] <= MAX_PRICE:
            m.bid          = ob["bid"]
            m.ask          = ob["ask"]
            m.spread_cents = ob["spread_cents"]
            m.bid_depth    = ob["bid_depth"]
            m.ask_depth    = ob["ask_depth"]
        else:
            # Pas de book valide → on skip ce marché
            continue

        # Filtre spread
        if m.spread_cents > MAX_SPREAD:
            continue

        # Oscillation
        trades = fetch_recent_trades(m.token_id_yes, limit=100)
        if trades:
            m.oscillation = analyze_oscillation(trades)

        # Score
        m.score = score_market(m)
        analyzed.append(m)

        time.sleep(0.1)  # rate limiting léger

    print(f"\r  {G}Analyse terminée — {len(analyzed)} marchés valides{R}{'':40}")

    # Tri par score
    analyzed.sort(key=lambda x: x.score, reverse=True)
    return analyzed[:top_n]


SPORT_KEYWORDS = [
    " vs ", " vs.", "vs. ", "match", " win on ", "beats ",
    "nba", "ipl", "nfl", "mlb", "nhl", "ufc", "mma", "fight night",
    "premier league", "champions league", "ligue 1", "bundesliga",
    "serie a", "la liga", "eredivisie", "ligue des champions",
    "cricket", "tennis", "open", "masters", "wimbledon", "roland garros",
    "formula 1", "motogp", "grand prix",
]
SPORT_FETCH_LIMIT = 700  # UFC etc. peuvent être hors top 300

def run_scanner_sport_du_jour(raw_markets: list = None) -> list:
    """
    Trouve les matchs sportifs se terminant dans les 12 prochaines heures.
    Triés par temps restant (plus urgent en premier).
    """
    if raw_markets is None:
        raw_markets = fetch_top_markets(limit=SPORT_FETCH_LIMIT)

    now     = datetime.now(timezone.utc)
    cutoff  = now + timedelta(hours=12)

    candidates = []
    for m in raw_markets:
        q         = m.get("question", "")
        end       = m.get("endDate", "") or m.get("end_date", "")
        outcome_p = m.get("outcomePrices", [])
        vol       = float(m.get("volume24hr") or 0)
        tokens    = m.get("clobTokenIds") or []

        if isinstance(tokens, str):
            try: tokens = _json.loads(tokens)
            except: continue
        if isinstance(outcome_p, str):
            try: outcome_p = _json.loads(outcome_p)
            except: continue

        if not tokens or len(tokens) < 2: continue
        if vol < 5_000: continue

        # Filtre sport
        q_lower = q.lower()
        if not any(kw in q_lower for kw in SPORT_KEYWORDS):
            continue

        # Parse timestamp complet
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except:
            continue

        # Seulement les matchs dans les 12 prochaines heures
        if end_dt <= now or end_dt > cutoff:
            continue

        try:
            yes_price = float(outcome_p[0]) if outcome_p else 0.5
        except:
            continue

        minutes_left = int((end_dt - now).total_seconds() / 60)
        h, mn = divmod(minutes_left, 60)
        time_left = f"{h}h{mn:02d}" if h > 0 else f"{mn}min"

        events     = m.get("events", [])
        event_slug = events[0].get("slug", "") if events else ""
        url_slug   = event_slug or m.get("slug", "")

        candidates.append({
            "question":     q,
            "slug":         url_slug,
            "token_id_yes": str(tokens[0]),
            "token_id_no":  str(tokens[1]),
            "yes_price":    yes_price,
            "volume_24h":   vol,
            "end_date":     end[:10],
            "minutes_left": minutes_left,
            "time_left":    time_left,
            "url":          f"https://polymarket.com/event/{url_slug}",
        })

    candidates.sort(key=lambda x: x["minutes_left"])

    # Enrichir avec le vrai orderbook pour tous les candidats
    results = []
    for c in candidates:
        ob = fetch_orderbook(c["token_id_yes"])
        if not ob:
            continue
        bid, ask = ob["bid"], ob["ask"]
        if bid < 0.10 or bid > 0.90:  # exclure prix extrêmes (NO implicite ou illiquide)
            continue
        shares = int(200 / bid) if bid > 0 else 0
        c["bid"]       = round(bid * 100, 1)
        c["ask"]       = round(ask * 100, 1)
        c["spread"]    = round(ob["spread_cents"], 2)
        c["bid_depth"] = round(ob["bid_depth"])
        c["ask_depth"] = round(ob["ask_depth"])
        c["shares"]    = shares
        c["profit"]    = round((ask - bid) * shares, 2)
        results.append(c)

    return results


def main():
    parser = argparse.ArgumentParser(description="Polymarket Volume Scanner")
    parser.add_argument("--whale",  action="store_true", help="Whale tracker uniquement")
    parser.add_argument("--watch",  action="store_true", help="Auto-refresh toutes les 60s")
    parser.add_argument("--top",    type=int, default=8, help="Nombre de marchés à afficher")
    parser.add_argument("--detail", action="store_true", help="Affichage détaillé")
    args = parser.parse_args()

    if args.whale:
        print_header()
        run_whale_tracker()
        return

    refresh_count = 0
    while True:
        refresh_count += 1
        print_header()

        if args.watch and refresh_count > 1:
            print(f"  {DG}Refresh #{refresh_count}{R}\n")

        # Scan
        top_markets = run_scanner(top_n=args.top)

        if not top_markets:
            print(f"\n{RE}Aucun marché trouvé avec les critères actuels.{R}")
        else:
            # Tableau récap
            print_summary_table(top_markets)

            # Cartes détaillées
            print(f"\n{B}{'═'*70}{R}")
            print(f"{B}  DÉTAIL — TOP {len(top_markets)} MARCHÉS{R}")
            print(f"{B}{'═'*70}{R}")
            for rank, m in enumerate(top_markets, 1):
                print_market_card(rank, m)

        # Whale tracker
        print(f"\n{'─'*70}")
        run_whale_tracker()

        # Résumé stratégie
        if top_markets:
            best = top_markets[0]
            print(f"\n{G}{B}  MEILLEUR MARCHÉ MAINTENANT :{R}")
            print(f"  {CY}{best.question[:60]}{R}")
            print(f"  BUY LIMIT {fmt_price(best.bid)}  →  "
                  f"SELL LIMIT {fmt_price(best.ask)}  "
                  f"(spread: {fmt_spread(best.spread_cents)})")
            print(f"  {DG}Pour ${TRADE_SIZE_USD} : {int(TRADE_SIZE_USD/best.bid) if best.bid > 0 else '?'} shares "
                  f"→ sell après 3-5 min{R}")

        if not args.watch:
            break

        print(f"\n{DG}⏱  Prochain refresh dans {WATCH_INTERVAL_SECONDS}s... (Ctrl+C pour arrêter){R}")
        try:
            time.sleep(WATCH_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print(f"\n{Y}Arrêt du scanner.{R}")
            break


if __name__ == "__main__":
    main()
