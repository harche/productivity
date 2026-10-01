import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "watch_comments.py"
SPEC = importlib.util.spec_from_file_location("watch_comments", SCRIPT)
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)


def thread(tid, *authors, status="open"):
    comments = [{"id": f"{tid}-c{i}", "author": a, "body": "text"} for i, a in enumerate(authors)]
    return {"id": tid, "file": "main.go", "line": 3, "status": status, "comments": comments}


class Clock:
    def __init__(self):
        self.value = 100

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class PendingTests(unittest.TestCase):
    def test_only_open_threads_whose_last_message_is_from_the_user(self):
        threads = [
            thread("a", "user"),
            thread("b", "user", "agent"),
            thread("c", "user", "agent", "user"),
            thread("d", "user", status="resolved"),
            thread("e"),
        ]
        got = watcher.pending(threads, set())
        self.assertEqual([(p["threadId"], p["commentId"]) for p in got], [("a", "a-c0"), ("c", "c-c2")])

    def test_acknowledged_comment_ids_are_skipped_but_new_follow_ups_are_not(self):
        threads = [thread("a", "user"), thread("c", "user", "agent", "user")]
        got = watcher.pending(threads, {"a-c0", "c-c0"})
        self.assertEqual([p["commentId"] for p in got], ["c-c2"])


class WatchTests(unittest.TestCase):
    def run_watch(self, responses, acknowledged=(), expires_at=110):
        clock = Clock()
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(watcher, "read_threads", side_effect=responses) as read,
            patch.object(watcher.time, "time", clock.now),
            patch.object(watcher.time, "monotonic", clock.now),
            patch.object(watcher.time, "sleep", clock.sleep),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = watcher.watch("/wt", set(acknowledged), expires_at)
        return code, json.loads(stdout.getvalue()), stderr.getvalue(), read

    def test_returns_batch_when_user_comment_appears(self):
        code, event, _, read = self.run_watch([[], [thread("a", "user")]])
        self.assertEqual(code, 0)
        self.assertEqual(event["event"], "treehouse_user_comments")
        self.assertEqual(event["root"], "/wt")
        self.assertEqual(event["threads"][0]["commentId"], "a-c0")
        self.assertEqual(read.call_count, 2)

    def test_rearm_catches_comments_added_while_replying(self):
        first = thread("a", "user")
        _, event, _, _ = self.run_watch([[first]])
        acknowledged = [t["commentId"] for t in event["threads"]]
        _, event, _, _ = self.run_watch([[first, thread("b", "user")]], acknowledged)
        self.assertEqual([t["threadId"] for t in event["threads"]], ["b"])

    def test_expires(self):
        code, event, _, _ = self.run_watch([[]] * 20, expires_at=103)
        self.assertEqual((code, event["event"]), (0, "treehouse_watch_expired"))

    def test_three_consecutive_failures_emit_error(self):
        code, event, stderr, _ = self.run_watch([ValueError("bad json")] * 3)
        self.assertEqual((code, event["event"]), (1, "treehouse_watch_error"))
        self.assertIn("poll failed (3/3)", stderr)

    def test_failure_counter_resets_after_success(self):
        responses = [ValueError("x"), ValueError("x"), [], ValueError("x"), [thread("a", "user")]]
        code, event, _, _ = self.run_watch(responses)
        self.assertEqual((code, event["event"]), (0, "treehouse_user_comments"))


class ArgTests(unittest.TestCase):
    def parse(self, *argv):
        with contextlib.redirect_stderr(io.StringIO()):
            return watcher.parse_args(list(argv))

    def test_rejects_relative_root_and_bad_acknowledged(self):
        for argv in (["--root", "rel", "--expires-at", "1"],
                     ["--root", "/", "--expires-at", "1", "--acknowledged-json", "{}"],
                     ["--root", "/", "--expires-at", "inf"]):
            with self.assertRaises(SystemExit):
                self.parse(*argv)

    def test_accepts_valid_args(self):
        args = self.parse("--root", "/", "--expires-at", "123", "--acknowledged-json", '["c1"]')
        self.assertEqual(args.acknowledged, {"c1"})


if __name__ == "__main__":
    unittest.main()
