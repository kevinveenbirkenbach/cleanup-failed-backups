#!/usr/bin/env python3
import io
import sys
import time
import tempfile
import unittest
import contextlib
from pathlib import Path
from unittest.mock import patch

# Import cleanup main.py
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import main  # noqa: E402

# Keep tests snappy but reliable:
# - "timeout" dirs sleep 0.3s in fake dirval
# - we pass --timeout 0.1s -> they will time out
FAKE_TIMEOUT_SLEEP = 0.3   # 300 ms
SHORT_TIMEOUT = "0.1"      # 100 ms

FAKE_DIRVAL = f"""#!/usr/bin/env python3
import sys, time, argparse, pathlib

def main():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--validate", action="store_true")
    args = p.parse_args()

    d = pathlib.Path(args.path)
    name = d.name.lower()

    # Simulate a slow validation for timeout* dirs
    if "timeout" in name:
        time.sleep({FAKE_TIMEOUT_SLEEP})
        print("Simulated long run...")
        return 0

    # VALID file -> success
    if (d / "VALID").exists():
        print("ok")
        return 0

    # otherwise -> fail
    print("failed")
    return 1

if __name__ == "__main__":
    sys.exit(main())
"""

class CleanupBackupsUsingDirvalTests(unittest.TestCase):
    def setUp(self):
        # temp /Backups root
        self.tmpdir = tempfile.TemporaryDirectory()
        self.backups_root = Path(self.tmpdir.name)

        # fake dirval on disk
        self.dirval = self.backups_root / "dirval"
        self.dirval.write_text(FAKE_DIRVAL, encoding="utf-8")
        self.dirval.chmod(0o755)

        # structure:
        # /Backups/ID1/backup-docker-to-local/{goodA, badB, timeoutC}
        # /Backups/ID2/backup-docker-to-local/{goodX, badY}
        self.id1 = self.backups_root / "ID1" / "backup-docker-to-local"
        self.id2 = self.backups_root / "ID2" / "backup-docker-to-local"
        for p in [self.id1, self.id2]:
            p.mkdir(parents=True, exist_ok=True)

        self.goodA = self.id1 / "goodA"
        self.badB = self.id1 / "badB"
        self.timeoutC = self.id1 / "timeoutC"
        self.goodX = self.id2 / "goodX"
        self.badY = self.id2 / "badY"
        for p in [self.goodA, self.badB, self.timeoutC, self.goodX, self.badY]:
            p.mkdir(parents=True, exist_ok=True)

        # mark valids
        (self.goodA / "VALID").write_text("1", encoding="utf-8")
        (self.goodX / "VALID").write_text("1", encoding="utf-8")

        # Capture stdout/stderr
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()
        self.stdout_cm = contextlib.redirect_stdout(self._stdout)
        self.stderr_cm = contextlib.redirect_stderr(self._stderr)
        self.stdout_cm.__enter__()
        self.stderr_cm.__enter__()

        # Patch BACKUPS_ROOT to temp root
        self.backups_patcher = patch.object(main, "BACKUPS_ROOT", self.backups_root)
        self.backups_patcher.start()

    def tearDown(self):
        self.backups_patcher.stop()
        self.stdout_cm.__exit__(None, None, None)
        self.stderr_cm.__exit__(None, None, None)
        self.tmpdir.cleanup()

    def run_main(self, argv):
        start = time.time()
        rc = main.main(argv)
        out = self._stdout.getvalue()
        err = self._stderr.getvalue()
        dur = time.time() - start
        self._stdout.seek(0); self._stdout.truncate(0)
        self._stderr.seek(0); self._stderr.truncate(0)
        return rc, out, err, dur

    def test_id_mode_yes_deletes_failures(self):
        rc, out, err, _ = self.run_main([
            "--id", "ID1",
            "--dirval-cmd", str(self.dirval),
            "--workers", "4",
            "--timeout", SHORT_TIMEOUT,
            "--yes",
        ])
        self.assertEqual(rc, 0, msg=err or out)
        self.assertTrue(self.goodA.exists(), "goodA should remain")
        self.assertFalse(self.badB.exists(), "badB should be deleted")
        self.assertFalse(self.timeoutC.exists(), "timeoutC should be deleted (timeout treated as failure)")
        self.assertIn("Summary:", out)

    def test_all_mode(self):
        rc, out, err, _ = self.run_main([
            "--all",
            "--dirval-cmd", str(self.dirval),
            "--workers", "4",
            "--timeout", SHORT_TIMEOUT,
            "--yes",
        ])
        self.assertEqual(rc, 0, msg=err or out)
        self.assertTrue(self.goodA.exists())
        self.assertFalse(self.badB.exists())
        self.assertFalse(self.timeoutC.exists())
        self.assertTrue(self.goodX.exists())
        self.assertFalse(self.badY.exists())

    def test_dirval_missing_errors(self):
        rc, out, err, _ = self.run_main([
            "--id", "ID1",
            "--dirval-cmd", str(self.backups_root / "nope-dirval"),
            "--timeout", SHORT_TIMEOUT,
            "--yes",
        ])
        self.assertEqual(rc, 0, msg=err or out)
        self.assertIn("dirval not found", out + err)

    def test_no_targets_message(self):
        empty = self.backups_root / "EMPTY" / "backup-docker-to-local"
        empty.mkdir(parents=True, exist_ok=True)
        rc, out, err, _ = self.run_main([
            "--id", "EMPTY",
            "--dirval-cmd", str(self.dirval),
            "--timeout", SHORT_TIMEOUT,
        ])
        self.assertEqual(rc, 0)
        self.assertIn("No subdirectories to validate. Nothing to do.", out)

    def test_interactive_keeps_when_no(self):
        with patch("builtins.input", return_value=""):
            rc, out, err, _ = self.run_main([
                "--id", "ID2",
                "--dirval-cmd", str(self.dirval),
                "--workers", "1",
                "--timeout", SHORT_TIMEOUT,
            ])
        self.assertEqual(rc, 0, msg=err or out)
        self.assertTrue(self.badY.exists(), "badY should be kept without confirmation")
        self.assertTrue(self.goodX.exists())

    def test_interactive_yes_deletes(self):
        with patch("builtins.input", return_value="y"):
            rc, out, err, _ = self.run_main([
                "--id", "ID2",
                "--dirval-cmd", str(self.dirval),
                "--workers", "1",
                "--timeout", SHORT_TIMEOUT,
            ])
        self.assertEqual(rc, 0, msg=err or out)
        self.assertFalse(self.badY.exists(), "badY should be deleted")
        self.assertTrue(self.goodX.exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)
