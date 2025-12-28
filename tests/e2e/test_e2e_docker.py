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


class CleanbackE2EDockerTests(unittest.TestCase):
    """
    E2E test that uses real directories, but runs inside a Docker container.
    It creates /Backups structure inside the container and invokes the app
    via `python -m cleanback`.
    """

    def setUp(self):
        # Create a real /Backups root inside the container
        # (safe because we are in Docker)
        self.backups_root = Path("/Backups")
        self.backups_root.mkdir(parents=True, exist_ok=True)

        # Use a unique run folder so repeated runs don't collide
        self.run_root = self.backups_root / f"E2E-{os.getpid()}"
        self.run_root.mkdir(parents=True, exist_ok=True)

        # Create fake `dirval` executable on disk (real file, real chmod)
        self.bin_dir = Path(tempfile.mkdtemp(prefix="cleanback-bin-"))
        self.dirval = self.bin_dir / "dirval"
        self.dirval.write_text(FAKE_DIRVAL, encoding="utf-8")
        self.dirval.chmod(0o755)

        # Create real backup directory structure
        # /Backups/<ID>/backup-docker-to-local/{good,bad,timeout}
        self.backup_id = "ID-E2E"
        self.base = self.run_root / self.backup_id / "backup-docker-to-local"
        self.base.mkdir(parents=True, exist_ok=True)

        self.good = self.base / "good"
        self.bad = self.base / "bad"
        self.timeout = self.base / "timeout"
        for p in (self.good, self.bad, self.timeout):
            p.mkdir(parents=True, exist_ok=True)

        (self.good / "VALID").write_text("1", encoding="utf-8")

    def tearDown(self):
        # Cleanup what we created inside /Backups
        # Keep it simple and robust (don't fail teardown)
        try:
            if self.run_root.exists():
                for p in sorted(self.run_root.rglob("*"), reverse=True):
                    try:
                        if p.is_dir():
                            p.rmdir()
                        else:
                            p.unlink()
                    except Exception:
                        pass
                try:
                    self.run_root.rmdir()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            # Remove temp bin dir
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

    def test_e2e_id_mode_yes_deletes_failures(self):
        env = os.environ.copy()

        # Prepend fake dirval path for this test run
        env["PATH"] = f"{self.bin_dir}:{env.get('PATH','')}"

        # Run: python -m cleanback --id <ID> --yes
        # We must point BACKUPS_ROOT to our run_root. Easiest: set /Backups = run_root
        # But code currently has BACKUPS_ROOT = /Backups constant.
        #
        # Therefore, we create our test tree under /Backups (done above) and pass --id
        # relative to that structure by using run_root/<ID>. To do that, we make
        # run_root the direct child under /Backups, then we pass the composite id:
        # "<run-folder>/<ID>".
        composite_id = f"{self.run_root.name}/{self.backup_id}"

        cmd = [
            "python", "-m", "cleanback",
            "--id", composite_id,
            "--dirval-cmd", "dirval",
            "--workers", "4",
            "--timeout", SHORT_TIMEOUT,
            "--yes",
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True, env=env)

        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertTrue(self.good.exists(), "good should remain")
        self.assertFalse(self.bad.exists(), "bad should be deleted")
        self.assertFalse(self.timeout.exists(), "timeout should be deleted (timeout treated as failure)")
        self.assertIn("Summary:", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
