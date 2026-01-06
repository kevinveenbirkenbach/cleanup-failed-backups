#!/usr/bin/env python3
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


FAKE_TIMEOUT_SLEEP = 0.3
SHORT_TIMEOUT = "0.1"

FAKE_DIRVAL = f"""#!/usr/bin/env python3
import sys, time, argparse, pathlib

def main():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--validate", action="store_true")
    args = p.parse_args()

    d = pathlib.Path(args.path)
    name = d.name.lower()

    if "timeout" in name:
        time.sleep({FAKE_TIMEOUT_SLEEP})
        print("Simulated long run...")
        return 0

    if (d / "VALID").exists():
        print("ok")
        return 0

    print("failed")
    return 1

if __name__ == "__main__":
    sys.exit(main())
"""


class CleanbackE2EForceKeepTests(unittest.TestCase):
    """
    E2E test that validates --force-keep in --all mode.

    The current behavior is:
    - In --all mode, cleanback discovers each /Backups/<ID>/backup-docker-to-local/*
    - Within each backup-docker-to-local folder, subdirs are sorted by name
    - With --force-keep N, the last N subdirs in that folder are skipped (kept)

    This test creates two backup folders under /Backups so --all can find them:
      /Backups/<prefix>-01/backup-docker-to-local/{good,bad}
      /Backups/<prefix>-02/backup-docker-to-local/{good,bad}

    With --force-keep 1:
    - In each folder, "good" is the last (sorted) and is skipped (kept)
    - "bad" is processed and deleted
    """

    def setUp(self):
        self.backups_root = Path("/Backups")
        self.backups_root.mkdir(parents=True, exist_ok=True)

        # Unique prefix to avoid collisions across runs
        self.prefix = f"E2EKEEP-{os.getpid()}"

        # Create fake `dirval` executable on disk (real file, real chmod)
        self.bin_dir = Path(tempfile.mkdtemp(prefix="cleanback-bin-"))
        self.dirval = self.bin_dir / "dirval"
        self.dirval.write_text(FAKE_DIRVAL, encoding="utf-8")
        self.dirval.chmod(0o755)

        # Two backup folders directly under /Backups (so --all can discover them)
        self.b1 = self.backups_root / f"{self.prefix}-01" / "backup-docker-to-local"
        self.b2 = self.backups_root / f"{self.prefix}-02" / "backup-docker-to-local"
        self.b1.mkdir(parents=True, exist_ok=True)
        self.b2.mkdir(parents=True, exist_ok=True)

        # Within each: good + bad
        self.b1_good = self.b1 / "good"
        self.b1_bad = self.b1 / "bad"
        self.b2_good = self.b2 / "good"
        self.b2_bad = self.b2 / "bad"

        for p in (self.b1_good, self.b1_bad, self.b2_good, self.b2_bad):
            p.mkdir(parents=True, exist_ok=True)

        # Mark goods as valid
        (self.b1_good / "VALID").write_text("1", encoding="utf-8")
        (self.b2_good / "VALID").write_text("1", encoding="utf-8")

        # Convenience for teardown
        self.created_roots = [
            self.backups_root / f"{self.prefix}-01",
            self.backups_root / f"{self.prefix}-02",
        ]

    def tearDown(self):
        # Cleanup created backup folders
        for root in self.created_roots:
            try:
                if root.exists():
                    for p in sorted(root.rglob("*"), reverse=True):
                        try:
                            if p.is_dir():
                                p.rmdir()
                            else:
                                p.unlink()
                        except Exception:
                            pass
                    try:
                        root.rmdir()
                    except Exception:
                        pass
            except Exception:
                pass

        # Cleanup temp bin dir
        try:
            if self.bin_dir.exists():
                for p in sorted(self.bin_dir.rglob("*"), reverse=True):
                    try:
                        if p.is_dir():
                            p.rmdir()
                        else:
                            p.unlink()
                    except Exception:
                        pass
                try:
                    self.bin_dir.rmdir()
                except Exception:
                    pass
        except Exception:
            pass

    def test_all_mode_force_keep_skips_last_timestamp_subdir_per_backup_folder(self):
        env = os.environ.copy()
        env["PATH"] = f"{self.bin_dir}:{env.get('PATH', '')}"

        cmd = [
            "python",
            "-m",
            "cleanback",
            "--backups-root",
            "/Backups",
            "--all",
            "--force-keep",
            "1",
            "--dirval-cmd",
            "dirval",
            "--workers",
            "4",
            "--timeout",
            SHORT_TIMEOUT,
            "--yes",
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True, env=env)

        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)

        # In each folder, sorted subdirs are: bad, good -> good is skipped, bad is processed
        self.assertTrue(self.b1_good.exists(), "b1 good should remain (skipped)")
        self.assertFalse(self.b1_bad.exists(), "b1 bad should be deleted")

        self.assertTrue(self.b2_good.exists(), "b2 good should remain (skipped)")
        self.assertFalse(self.b2_bad.exists(), "b2 bad should be deleted")

        self.assertIn("Summary:", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
