"""Tests for iron_butterfly.py strategy logic."""

from iron_butterfly import round_to_strike, parse_expiry, display_strategy, build_combo_contract, STRATEGIES
from datetime import date, datetime
from ib_async import Contract


class TestRoundToStrike:
    def test_rounds_to_5(self):
        assert round_to_strike(7473) == 7475

    def test_exact(self):
        assert round_to_strike(7475) == 7475

    def test_rounds_down(self):
        assert round_to_strike(7472) == 7470

    def test_zero(self):
        assert round_to_strike(0) == 0


class TestParseExpiry:
    def test_today(self):
        result = parse_expiry("today")
        assert result == datetime.now().date()

    def test_tomorrow(self):
        result = parse_expiry("tomorrow")
        expected = datetime.now().date()
        assert (result - expected).days == 1

    def test_date_string(self):
        result = parse_expiry("2026-06-15")
        assert result == date(2026, 6, 15)


class TestStrategies:
    def test_strategy_1_is_butterfly(self):
        s = STRATEGIES[1]
        assert s["short_offset"] == 0.0
        assert s["profit_target_pct"] is None

    def test_strategy_3_is_condor_with_tp(self):
        s = STRATEGIES[3]
        assert s["short_offset"] == 0.3
        assert s["profit_target_pct"] == 0.6

    def test_all_strategies_have_ratio(self):
        for key, s in STRATEGIES.items():
            assert "ratio" in s
            assert s["ratio"] > 0


class TestBuildComboContract:
    def test_builds_bag(self, sample_strategy):
        bag = build_combo_contract(sample_strategy)
        assert bag.secType == "BAG"
        assert bag.symbol == "SPX"
        assert len(bag.comboLegs) == 4

    def test_leg_actions_correct(self, sample_strategy):
        bag = build_combo_contract(sample_strategy)
        actions = [leg.action for leg in bag.comboLegs]
        assert actions == ["BUY", "SELL", "SELL", "BUY"]

    def test_leg_conids_match(self, sample_strategy):
        bag = build_combo_contract(sample_strategy)
        conids = [leg.conId for leg in bag.comboLegs]
        expected = [leg["conid"] for leg in sample_strategy["legs"]]
        assert conids == expected


class TestDisplayStrategy:
    def test_no_crash(self, sample_strategy, capsys):
        display_strategy(sample_strategy, quantity=1, strategy_num=1)
        captured = capsys.readouterr()
        assert "IRON BUTTERFLY" in captured.out
        assert "42.50" in captured.out

    def test_condor_label(self, sample_strategy, capsys):
        sample_strategy["strategy_name"] = "iron_condor"
        display_strategy(sample_strategy, quantity=1)
        captured = capsys.readouterr()
        assert "IRON CONDOR" in captured.out
