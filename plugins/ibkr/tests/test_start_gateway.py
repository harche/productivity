"""Tests for start_gateway.py — gateway discovery and startup."""

import os
from unittest.mock import patch, MagicMock

import pytest

import start_gateway as sg


# ---------------------------------------------------------------------------
# Gateway discovery tests
# ---------------------------------------------------------------------------

class TestFindGateway:
    def test_finds_gateway_at_first_path(self, tmp_path):
        gw_dir = tmp_path / "ibkr"
        (gw_dir / "bin").mkdir(parents=True)
        (gw_dir / "root").mkdir(parents=True)
        (gw_dir / "bin" / "run.sh").write_text("#!/bin/bash")
        (gw_dir / "root" / "conf.yaml").write_text("config: true")

        with patch.object(sg, "SEARCH_PATHS", [str(gw_dir), "/nonexistent"]):
            result = sg.find_gateway()

        assert result == str(gw_dir)

    def test_skips_incomplete_paths(self, tmp_path):
        # Has bin/run.sh but no root/conf.yaml
        gw_dir = tmp_path / "incomplete"
        (gw_dir / "bin").mkdir(parents=True)
        (gw_dir / "bin" / "run.sh").write_text("#!/bin/bash")

        with patch.object(sg, "SEARCH_PATHS", [str(gw_dir)]):
            result = sg.find_gateway()

        assert result is None

    def test_returns_none_when_not_found(self):
        with patch.object(sg, "SEARCH_PATHS", ["/nonexistent1", "/nonexistent2"]):
            result = sg.find_gateway()

        assert result is None

    def test_finds_second_path(self, tmp_path):
        gw_dir = tmp_path / "clientportal.gw"
        (gw_dir / "bin").mkdir(parents=True)
        (gw_dir / "root").mkdir(parents=True)
        (gw_dir / "bin" / "run.sh").write_text("#!/bin/bash")
        (gw_dir / "root" / "conf.yaml").write_text("config: true")

        with patch.object(sg, "SEARCH_PATHS", ["/nonexistent", str(gw_dir)]):
            result = sg.find_gateway()

        assert result == str(gw_dir)


# ---------------------------------------------------------------------------
# Port check tests
# ---------------------------------------------------------------------------

class TestIsPortOpen:
    @patch("start_gateway.socket.socket")
    def test_port_open(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket_cls.return_value = mock_socket

        assert sg.is_port_open(5000) is True

    @patch("start_gateway.socket.socket")
    def test_port_closed(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket_cls.return_value = mock_socket

        assert sg.is_port_open(5000) is False


# ---------------------------------------------------------------------------
# Auth check tests
# ---------------------------------------------------------------------------

class TestCheckAuth:
    @patch("urllib.request.urlopen")
    def test_authenticated(self, mock_urlopen):
        import json
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"authenticated": True}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = sg.check_auth()
        assert result["authenticated"] is True

    @patch("urllib.request.urlopen")
    def test_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")

        result = sg.check_auth()
        assert result is None


# ---------------------------------------------------------------------------
# Main flow tests
# ---------------------------------------------------------------------------

class TestMain:
    @patch("start_gateway.check_auth")
    @patch("start_gateway.is_port_open")
    def test_already_running(self, mock_port, mock_auth, capsys):
        mock_port.return_value = True
        mock_auth.return_value = {"authenticated": True}

        with patch("sys.argv", ["start_gateway.py"]):
            sg.main()

        output = capsys.readouterr().out
        assert "already running" in output

    @patch("start_gateway.is_port_open")
    @patch("start_gateway.find_gateway")
    def test_gateway_not_found_exits(self, mock_find, mock_port):
        mock_port.return_value = False
        mock_find.return_value = None

        with patch("sys.argv", ["start_gateway.py"]):
            with pytest.raises(SystemExit):
                sg.main()

    @patch("start_gateway.time.sleep")
    @patch("start_gateway.subprocess.Popen")
    @patch("start_gateway.is_port_open")
    @patch("start_gateway.find_gateway")
    def test_starts_and_waits(self, mock_find, mock_port, mock_popen, mock_sleep, tmp_path, capsys):
        gw_dir = str(tmp_path / "ibkr")
        os.makedirs(os.path.join(gw_dir, "bin"))
        os.makedirs(os.path.join(gw_dir, "root"))
        with open(os.path.join(gw_dir, "bin", "run.sh"), "w") as f:
            f.write("#!/bin/bash")
        with open(os.path.join(gw_dir, "root", "conf.yaml"), "w") as f:
            f.write("config: true")

        mock_find.return_value = gw_dir
        # Port closed initially, then open after startup
        mock_port.side_effect = [False, False, True]

        with patch("sys.argv", ["start_gateway.py"]):
            sg.main()

        output = capsys.readouterr().out
        assert "Found gateway" in output
        assert "ready" in output
        mock_popen.assert_called_once()
