"""Tests for ibkr_client.py — shared client module."""

from unittest.mock import patch, MagicMock
import time

import pytest

import ibkr_client as client


# ---------------------------------------------------------------------------
# parse_price tests
# ---------------------------------------------------------------------------

class TestParsePrice:
    def test_none(self) -> None:
        assert client.parse_price(None) is None

    def test_int(self) -> None:
        assert client.parse_price(42) == 42.0

    def test_float(self) -> None:
        assert client.parse_price(42.5) == 42.5

    def test_string_number(self) -> None:
        assert client.parse_price("42.50") == 42.5

    def test_string_with_c_prefix(self) -> None:
        assert client.parse_price("C42.50") == 42.5

    def test_string_with_h_prefix(self) -> None:
        assert client.parse_price("H100.00") == 100.0

    def test_invalid_string(self) -> None:
        assert client.parse_price("N/A") is None

    def test_empty_string(self) -> None:
        assert client.parse_price("") is None


# ---------------------------------------------------------------------------
# API retry tests
# ---------------------------------------------------------------------------

class TestApiGet:
    @patch("ibkr_client.requests.get")
    def test_retries_on_500(self, mock_get: MagicMock) -> None:
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"data": "ok"}
        ok_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [fail_resp, ok_resp]

        with patch("ibkr_client.time.sleep"):
            result = client.api_get("/test")

        assert result == {"data": "ok"}
        assert mock_get.call_count == 2

    @patch("ibkr_client.requests.get")
    def test_raises_after_max_retries(self, mock_get: MagicMock) -> None:
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.raise_for_status.side_effect = Exception("500 Server Error")

        mock_get.return_value = fail_resp

        with patch("ibkr_client.time.sleep"):
            with pytest.raises(Exception, match="500"):
                client.api_get("/test", retries=2)

        assert mock_get.call_count == 3

    @patch("ibkr_client.requests.get")
    def test_no_retry_on_4xx(self, mock_get: MagicMock) -> None:
        fail_resp = MagicMock()
        fail_resp.status_code = 400
        fail_resp.raise_for_status.side_effect = Exception("400 Bad Request")

        mock_get.return_value = fail_resp

        with pytest.raises(Exception, match="400"):
            client.api_get("/test")

        assert mock_get.call_count == 1

    @patch("ibkr_client.requests.get")
    def test_raises_on_401(self, mock_get: MagicMock) -> None:
        resp = MagicMock()
        resp.status_code = 401

        mock_get.return_value = resp

        with pytest.raises(ConnectionError, match="Session expired"):
            client.api_get("/test")


class TestApiPost:
    @patch("ibkr_client.requests.post")
    def test_retries_on_500(self, mock_post: MagicMock) -> None:
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"order_id": "123"}
        ok_resp.raise_for_status = MagicMock()

        mock_post.side_effect = [fail_resp, ok_resp]

        with patch("ibkr_client.time.sleep"):
            result = client.api_post("/test")

        assert result == {"order_id": "123"}

    @patch("ibkr_client.requests.post")
    def test_raises_on_401(self, mock_post: MagicMock) -> None:
        resp = MagicMock()
        resp.status_code = 401

        mock_post.return_value = resp

        with pytest.raises(ConnectionError, match="Session expired"):
            client.api_post("/test")


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------

class TestInitializeSession:
    @patch("ibkr_client.api_get")
    def test_authenticated(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = [
            {"accounts": ["DUXXXXXXX"]},
            {"authenticated": True, "connected": True},
        ]
        with patch("ibkr_client.time.sleep"):
            status = client.initialize_session()
        assert status["authenticated"] is True

    @patch("ibkr_client.api_get")
    def test_not_authenticated_exits(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = [
            {"accounts": ["DUXXXXXXX"]},
            {"authenticated": False, "connected": True},
        ]
        with patch("ibkr_client.time.sleep"):
            with pytest.raises(SystemExit):
                client.initialize_session()


# ---------------------------------------------------------------------------
# Market snapshot tests
# ---------------------------------------------------------------------------

class TestGetMarketSnapshot:
    @patch("ibkr_client.api_get")
    def test_returns_parsed_data(self, mock_get: MagicMock) -> None:
        now_ms = int(time.time() * 1000)
        mock_get.side_effect = [
            [{"conid": 111}],  # prime
            [{"conid": 111, "84": "20.5", "86": "20.7", "31": "20.6", "_updated": now_ms}],
        ]

        with patch("ibkr_client.time.sleep"):
            result = client.get_market_snapshot([111])

        assert result[111]["bid"] == 20.5
        assert result[111]["ask"] == 20.7
        assert result[111]["last"] == 20.6
        assert result[111]["_stale"] is False

    @patch("ibkr_client.api_get")
    def test_detects_stale_data(self, mock_get: MagicMock) -> None:
        old_ms = int(time.time() * 1000) - 30000  # 30 seconds old
        mock_get.side_effect = [
            [{"conid": 111}],
            [{"conid": 111, "84": "20.5", "86": "20.7", "31": "20.6", "_updated": old_ms}],
        ]

        with patch("ibkr_client.time.sleep"):
            result = client.get_market_snapshot([111])

        assert result[111]["_stale"] is True


class TestCheckStaleness:
    def test_no_stale(self) -> None:
        snapshots = {111: {"_stale": False}, 222: {"_stale": False}}
        assert client.check_staleness(snapshots) == []

    def test_some_stale(self) -> None:
        snapshots = {111: {"_stale": True}, 222: {"_stale": False}}
        assert client.check_staleness(snapshots) == [111]


# ---------------------------------------------------------------------------
# Order handling tests
# ---------------------------------------------------------------------------

class TestHandleOrderResponse:
    @patch("ibkr_client.api_post")
    def test_direct_success(self, mock_post: MagicMock) -> None:
        resp = [{"order_id": "12345", "order_status": "Filled"}]
        assert client.handle_order_response(resp) == "12345"

    @patch("ibkr_client.api_post")
    def test_with_confirmation(self, mock_post: MagicMock) -> None:
        mock_post.return_value = [{"order_id": "12345", "order_status": "Filled"}]
        resp = [{"id": "conf1", "message": ["Are you sure?"]}]
        assert client.handle_order_response(resp) == "12345"

    @patch("ibkr_client.api_post")
    def test_multiple_confirmations(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = [
            [{"id": "conf2", "message": ["Confirm?"]}],
            [{"order_id": "12345", "order_status": "Filled"}],
        ]
        resp = [{"id": "conf1", "message": ["Price exceeds limit"]}]
        assert client.handle_order_response(resp) == "12345"

    def test_error_returns_none(self) -> None:
        resp = [{"error": "Insufficient funds"}]
        assert client.handle_order_response(resp) is None

    def test_empty_response(self) -> None:
        assert client.handle_order_response([]) is None

    def test_non_list_response(self) -> None:
        assert client.handle_order_response({}) is None


# ---------------------------------------------------------------------------
# Contract search tests
# ---------------------------------------------------------------------------

class TestSearchContract:
    @patch("ibkr_client.api_get")
    def test_finds_contract(self, mock_get: MagicMock) -> None:
        mock_get.return_value = {
            "AAPL": [{"name": "APPLE INC", "contracts": [{"conid": 265598, "exchange": "NASDAQ"}]}]
        }
        result = client.search_contract("AAPL")
        assert result["conid"] == 265598

    @patch("ibkr_client.api_get")
    def test_raises_on_not_found(self, mock_get: MagicMock) -> None:
        mock_get.return_value = {"XYZ": []}
        with pytest.raises(ValueError, match="No contracts found"):
            client.search_contract("XYZ")

    @patch("ibkr_client.api_get")
    def test_raises_on_no_contracts_key(self, mock_get: MagicMock) -> None:
        mock_get.return_value = {"XYZ": [{"name": "test", "contracts": []}]}
        with pytest.raises(ValueError, match="No contracts found"):
            client.search_contract("XYZ")


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    @patch("ibkr_client.api_get")
    def test_get_market_snapshot_single_dict_response(self, mock_get: MagicMock) -> None:
        """API sometimes returns a single dict instead of a list."""
        now_ms = int(time.time() * 1000)
        mock_get.side_effect = [
            {"conid": 111},  # single dict prime
            {"conid": 111, "84": "20.0", "86": "20.2", "31": "20.1", "_updated": now_ms},
        ]

        with patch("ibkr_client.time.sleep"):
            result = client.get_market_snapshot([111])

        assert 111 in result

    @patch("ibkr_client.api_get")
    def test_get_account_id_empty_exits(self, mock_get: MagicMock) -> None:
        mock_get.return_value = []
        with pytest.raises(SystemExit):
            client.get_account_id()

    @patch("ibkr_client.api_get")
    def test_get_option_contract_no_match(self, mock_get: MagicMock) -> None:
        mock_get.return_value = [{"maturityDate": "20260312", "tradingClass": "SPXW", "conid": 123}]
        with patch("ibkr_client.time.sleep"):
            with pytest.raises(ValueError, match="No option contract found"):
                client.get_option_contract(416904, 6780, "P", "MAR26", "20260311")

    @patch("ibkr_client.api_get")
    def test_get_option_contract_prefers_spxw(self, mock_get: MagicMock) -> None:
        mock_get.return_value = [
            {"maturityDate": "20260311", "tradingClass": "SPX", "conid": 111},
            {"maturityDate": "20260311", "tradingClass": "SPXW", "conid": 222},
        ]
        with patch("ibkr_client.time.sleep"):
            result = client.get_option_contract(416904, 6780, "P", "MAR26", "20260311")
        assert result["conid"] == 222
