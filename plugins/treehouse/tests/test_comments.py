import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "comments.py"


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "main.go").write_text("package main\n\nfunc a() {}\n")

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, stdin=None):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args],
                                capture_output=True, text=True, input=stdin)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def store(self):
        return json.loads((self.root / ".treehouse" / "comments.json").read_text())

    def test_add_reply_resolve_round_trip(self):
        tid = self.cli("add", "--file", "main.go", "--line", "3", "flag this").split()[-1]
        thread = self.store()["threads"][0]
        self.assertEqual(thread["anchor"]["text"], "func a() {}")
        self.assertEqual((self.root / ".treehouse" / ".gitignore").read_text(), "*\n")

        # Simulate the user answering in VS Code, which makes the thread pending again.
        data = self.store()
        data["threads"][0]["comments"].append({"id": "u1", "author": "user", "body": "why?"})
        (self.root / ".treehouse" / "comments.json").write_text(json.dumps(data))
        self.assertIn("awaiting agent", self.cli("pending"))

        self.cli("reply", tid[:6], "-", stdin="because\n")
        self.assertEqual(self.cli("pending").strip(), "no threads")
        self.assertEqual(self.store()["threads"][0]["comments"][-1]["body"], "because")

        self.cli("resolve", tid)
        self.assertEqual(self.cli("list").strip(), "no threads")
        self.assertIn(tid, self.cli("list", "--all"))

    def test_missing_store_lists_nothing(self):
        self.assertEqual(self.cli("list").strip(), "no threads")


if __name__ == "__main__":
    unittest.main()
