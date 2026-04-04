#!/usr/bin/env python3
"""
Tests automatisés — Polymarket Volume Scanner
Lance avec : python3 tests.py
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# ─── Import du scanner ────────────────────────────────────────────────────────
from polymarket_scanner import (
    analyze_oscillation,
    score_market,
    is_on_avoid_list,
    is_expired_or_today,
    fmt_price,
    fmt_volume,
    MarketOpportunity,
    OscillationData,
)


# ─── Tests utilitaires ────────────────────────────────────────────────────────
class TestFormatters(unittest.TestCase):

    def test_fmt_price_cents(self):
        self.assertEqual(fmt_price(0.134), "13.4¢")

    def test_fmt_price_near_one(self):
        self.assertEqual(fmt_price(0.95), "95.0¢")

    def test_fmt_volume_millions(self):
        result = fmt_volume(1_500_000)
        self.assertIn("1.5M", result)

    def test_fmt_volume_thousands(self):
        result = fmt_volume(75_000)
        self.assertIn("75k", result)


# ─── Tests filtres marché ─────────────────────────────────────────────────────
class TestAvoidList(unittest.TestCase):

    def test_avoid_iran(self):
        self.assertTrue(is_on_avoid_list("US forces enter Iran by April 30?"))

    def test_avoid_case_insensitive(self):
        self.assertTrue(is_on_avoid_list("IRAN nuclear deal"))

    def test_normal_market_not_avoided(self):
        self.assertFalse(is_on_avoid_list("Will France win the 2026 World Cup?"))

    def test_ipl_not_avoided(self):
        self.assertFalse(is_on_avoid_list("IPL 2026: RCB vs CSK"))


class TestExpiredFilter(unittest.TestCase):

    def test_past_date_filtered(self):
        self.assertTrue(is_expired_or_today("2024-01-01T00:00:00Z"))

    def test_today_filtered(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.assertTrue(is_expired_or_today(f"{today}T23:59:59Z"))

    def test_future_date_not_filtered(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertFalse(is_expired_or_today(f"{future}T00:00:00Z"))


# ─── Tests oscillation ────────────────────────────────────────────────────────
class TestOscillation(unittest.TestCase):

    def _make_trades(self, prices):
        """Crée une liste de trades simulés."""
        return [{"price": str(p), "side": "BUY", "size": "100"} for p in prices]

    def test_no_trades_returns_none(self):
        result = analyze_oscillation([])
        self.assertIsNone(result)

    def test_flat_market_zero_reversals(self):
        # Marché plat = aucun reversal (pas de changement de direction)
        trades = self._make_trades([0.50] * 20)
        result = analyze_oscillation(trades)
        if result:
            self.assertEqual(result.num_reversals, 0)

    def test_bouncing_market_high_score(self):
        # Marché qui bounce régulièrement = bonne oscillation
        prices = [0.48, 0.52, 0.48, 0.52, 0.48, 0.52, 0.48, 0.52,
                  0.48, 0.52, 0.48, 0.52, 0.48, 0.52, 0.48, 0.52]
        trades = self._make_trades(prices)
        result = analyze_oscillation(trades)
        if result:
            self.assertGreater(result.score, 0.3)

    def test_oscillation_range_correct(self):
        prices = [0.48, 0.52, 0.48, 0.52, 0.48, 0.52, 0.48, 0.52,
                  0.48, 0.52, 0.48, 0.52, 0.48, 0.52, 0.48, 0.52]
        trades = self._make_trades(prices)
        result = analyze_oscillation(trades)
        if result:
            # Range doit être ~4 cents (0.52 - 0.48 = 0.04 → 4 ticks de 0.01)
            self.assertAlmostEqual(result.range_ticks, 4.0, delta=1.0)


# ─── Tests scoring ────────────────────────────────────────────────────────────
class TestScoring(unittest.TestCase):

    def _make_market(self, bid, ask, volume, yes_price=0.5):
        """Crée un MarketOpportunity de test."""
        m = MarketOpportunity(
            question="Test market",
            slug="test-market",
            token_id_yes="0x1234",
            token_id_no="0x5678",
            volume_24h=volume,
            yes_price=yes_price,
            end_date="2026-12-31",
        )
        m.bid = bid
        m.ask = ask
        m.spread_cents = (ask - bid) * 100
        m.bid_depth = 5000
        m.ask_depth = 5000
        return m

    def test_tight_spread_scores_higher(self):
        good = self._make_market(0.498, 0.502, 500_000)  # 0.4¢ spread
        bad  = self._make_market(0.490, 0.510, 500_000)  # 2¢ spread
        self.assertGreater(score_market(good), score_market(bad))

    def test_high_volume_scores_higher(self):
        high_vol = self._make_market(0.498, 0.502, 1_000_000)
        low_vol  = self._make_market(0.498, 0.502, 50_000)
        self.assertGreater(score_market(high_vol), score_market(low_vol))

    def test_extreme_price_scores_lower(self):
        mid   = self._make_market(0.498, 0.502, 500_000, yes_price=0.50)
        extreme = self._make_market(0.088, 0.092, 500_000, yes_price=0.09)
        self.assertGreater(score_market(mid), score_market(extreme))

    def test_score_between_0_and_100(self):
        m = self._make_market(0.498, 0.502, 500_000)
        s = score_market(m)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)


# ─── Tests API (avec mocks) ───────────────────────────────────────────────────
class TestAPIWithMocks(unittest.TestCase):

    @patch("polymarket_scanner.requests.get")
    def test_fetch_orderbook_returns_none_on_error(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        from polymarket_scanner import fetch_orderbook
        result = fetch_orderbook("0xFAKETOKEN")
        self.assertIsNone(result)

    @patch("polymarket_scanner.requests.get")
    def test_fetch_orderbook_parses_bid_ask(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "bids": [{"price": "0.48", "size": "1000"}, {"price": "0.47", "size": "500"}],
            "asks": [{"price": "0.52", "size": "800"}, {"price": "0.53", "size": "300"}],
        }
        mock_get.return_value = mock_response

        from polymarket_scanner import fetch_orderbook
        result = fetch_orderbook("0xTESTTOKEN")

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["bid"], 0.48, places=2)
        self.assertAlmostEqual(result["ask"], 0.52, places=2)
        self.assertAlmostEqual(result["spread_cents"], 4.0, delta=0.5)


# ─── Runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  POLYMARKET SCANNER — Tests automatisés")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
