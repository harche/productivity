import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "watch_comments.py"
SPEC = importlib.util.spec_from_file_location("watch_comments", SCRIPT)
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)


def note(note_id, source="user"):
    return {"noteId": note_id, "source": source, "body": "A question", "newRange": [49, 49]}


class Clock:
    def __init__(self):
        self.value = 100

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class WatchTests(unittest.TestCase):
    def run_watch(self, responses, acknowledged=(), expires_at=110):
        clock = Clock()
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(watcher, "read_comments", side_effect=responses) as read,
            patch.object(watcher.time, "time", clock.now),
            patch.object(watcher.time, "monotonic", clock.now),
            patch.object(watcher.time, "sleep", clock.sleep),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = watcher.watch("pinned-session", set(acknowledged), expires_at)
        return code, json.loads(stdout.getvalue()), stderr.getvalue(), read

    def test_returns_batch_without_acknowledged_notes(self):
        pending = [note("new-a"), note("new-b")]
        code, event, _, read = self.run_watch([[note("old"), *pending]], ["old"])
        self.assertEqual(code, 0)
        self.assertEqual(event, {
            "event": "hunk_user_comments", "sessionId": "pinned-session", "comments": pending,
        })
        read.assert_called_once_with("pinned-session", timeout=10)

    def test_rearm_catches_comments_added_while_replying(self):
        first = note("first")
        _, event, _, _ = self.run_watch([[first]])
        acknowledged = [item["noteId"] for item in event["comments"]]
        _, event, _, _ = self.run_watch([[first, note("arrived-during-reply")]], acknowledged)
        self.assertEqual([item["noteId"] for item in event["comments"]], ["arrived-during-reply"])

    def test_waits_through_empty_and_acknowledged_snapshots(self):
        code, event, _, read = self.run_watch([[], [note("old")], [note("new")]], ["old"])
        self.assertEqual(code, 0)
        self.assertEqual(event["comments"], [note("new")])
        self.assertEqual(read.call_count, 3)

    def test_already_expired_does_not_poll(self):
        code, event, _, read = self.run_watch([], expires_at=99)
        self.assertEqual(code, 0)
        self.assertEqual(event["event"], "hunk_watch_expired")
        read.assert_not_called()

    def test_deadline_limits_poll_and_sleep(self):
        code, event, _, read = self.run_watch([[], []], expires_at=103)
        self.assertEqual(code, 0)
        self.assertEqual(event["event"], "hunk_watch_expired")
        self.assertEqual([call.kwargs["timeout"] for call in read.call_args_list], [3, 1])

    def test_three_failures_stop_with_actionable_error(self):
        failures = [FileNotFoundError("hunk missing"), ValueError("invalid JSON"),
                    subprocess.TimeoutExpired("hunk", 10)]
        code, event, stderr, read = self.run_watch(failures)
        self.assertEqual(code, 1)
        self.assertEqual(event["event"], "hunk_watch_error")
        self.assertIn("daemon", event["action"])
        self.assertIn("(3/3)", stderr)
        self.assertEqual(read.call_count, 3)

    def test_successful_poll_resets_consecutive_failures(self):
        failure = ValueError("unreachable")
        code, event, _, _ = self.run_watch(
            [failure, failure, [], failure, failure, [note("new")]], expires_at=120,
        )
        self.assertEqual(code, 0)
        self.assertEqual(event["event"], "hunk_user_comments")


class ReadTests(unittest.TestCase):
    def test_pins_cli_session_and_excludes_agent_notes(self):
        result = subprocess.CompletedProcess([], 0, json.dumps({
            "comments": [note("human"), note("reply", source="agent")],
        }), "")
        with patch.object(watcher.subprocess, "run", return_value=result) as run:
            self.assertEqual(watcher.read_comments("session-id", 4), [note("human")])
        run.assert_called_once_with(
            ["hunk", "session", "comment", "list", "session-id", "--type", "user", "--json"],
            capture_output=True, text=True, timeout=4,
        )

    def test_rejects_malformed_snapshots(self):
        for output in ["not json", "[]", "{}", '{"comments":{}}',
                       '{"comments":[null]}', '{"comments":[{"noteId":null}]}']:
            with self.subTest(output=output):
                result = subprocess.CompletedProcess([], 0, output, "")
                with patch.object(watcher.subprocess, "run", return_value=result):
                    with self.assertRaises(ValueError):
                        watcher.read_comments("session-id", 10)

    def test_preserves_cli_error(self):
        result = subprocess.CompletedProcess([], 1, "", "No active Hunk sessions")
        with patch.object(watcher.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(ValueError, "No active Hunk sessions"):
                watcher.read_comments("session-id", 10)


class ArgumentTests(unittest.TestCase):
    def test_defaults_and_acknowledged_ids(self):
        args = watcher.parse_args([
            "--session", "session-id", "--expires-at", "1000",
            "--acknowledged-json", '["old", "old"]',
        ])
        self.assertEqual(args.acknowledged, {"old"})
        self.assertEqual(args.interval, 2)

    def test_rejects_invalid_arguments(self):
        invalid = [
            ["--acknowledged-json", "not json"], ["--acknowledged-json", "{}"],
            ["--acknowledged-json", "[1]"], ["--acknowledged-json", '[""]'],
            ["--expires-at", "nan"], ["--expires-at", "inf"], ["--expires-at", "later"],
            ["--interval", "0"], ["--interval", "-1"], ["--interval", "nan"],
            ["--session="], ["--session=--repo"],
        ]
        for options in invalid:
            with self.subTest(options=options), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    watcher.parse_args(["--session", "session-id", "--expires-at", "1000", *options])
                self.assertEqual(error.exception.code, 2)

    def test_cancellation_event(self):
        stdout = io.StringIO()
        with patch.object(watcher, "watch", side_effect=KeyboardInterrupt), contextlib.redirect_stdout(stdout):
            code = watcher.main(["--session", "session-id", "--expires-at", "1000"])
        self.assertEqual(code, 130)
        self.assertEqual(json.loads(stdout.getvalue())["event"], "hunk_watch_cancelled")


if __name__ == "__main__":
    unittest.main()
