#!/usr/bin/env python3
"""
Cleanup Failed Docker Backups — parallel validator (using dirval)
with optional "keep last N backups" behavior in --all mode.

Validates backup subdirectories under:
- <BACKUPS_ROOT>/<ID>/backup-docker-to-local          (when --id is used)
- <BACKUPS_ROOT>/*/backup-docker-to-local             (when --all is used)

For each subdirectory:
- Runs `dirval <subdir> --validate`.
- If validation fails, it lists the contents and asks whether to delete.
- With --yes, deletions happen automatically (no prompt).

Parallelism:
- Validation runs in parallel (thread pool). Deletions are performed afterwards
  sequentially (to keep prompts sane).
"""

from __future__ import annotations

import argparse
import multiprocessing
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ValidationResult:
    subdir: Path
    ok: bool
    returncode: int
    stderr: str
    stdout: str


def discover_target_subdirs(
    backups_root: Path, backup_id: Optional[str], all_mode: bool, force_keep: int
) -> List[Path]:
    """
    Return a list of subdirectories to validate:
      - If backup_id is given: <root>/<id>/backup-docker-to-local/* (dirs only)
      - If --all: for each <root>/* that has backup-docker-to-local, include its subdirs
    """
    targets: List[Path] = []
    if force_keep < 0:
        raise ValueError("--force-keep must be >= 0")

    if not backups_root.is_dir():
        raise FileNotFoundError(f"Backups root does not exist: {backups_root}")

    if all_mode:
        backup_folders = sorted(p for p in backups_root.iterdir() if p.is_dir())

        # Skip the last N backup folders (by sorted name order).
        # This is intentionally simple: timestamp-like folder names sort correctly.
        if force_keep:
            if len(backup_folders) <= force_keep:
                return []
            backup_folders = backup_folders[:-force_keep]

        for backup_folder in backup_folders:
            candidate = backup_folder / "backup-docker-to-local"
            if candidate.is_dir():
                targets.extend(sorted([p for p in candidate.iterdir() if p.is_dir()]))
    else:
        if not backup_id:
            raise ValueError("Either --id or --all must be provided.")
        base = backups_root / backup_id / "backup-docker-to-local"
        if not base.is_dir():
            raise FileNotFoundError(f"Directory does not exist: {base}")
        targets = sorted([p for p in base.iterdir() if p.is_dir()])

    return targets


def run_dirval_validate(
    subdir: Path, dirval_cmd: str, timeout: float
) -> ValidationResult:
    """
    Execute dirval:
        <dirval_cmd> "<SUBDIR>" --validate
    Return ValidationResult with ok = (returncode == 0).
    """
    cmd = [dirval_cmd, str(subdir), "--validate"]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
            timeout=timeout,
        )
        return ValidationResult(
            subdir=subdir,
            ok=(proc.returncode == 0),
            returncode=proc.returncode,
            stderr=(proc.stderr or "").strip(),
            stdout=(proc.stdout or "").strip(),
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(
            subdir=subdir,
            ok=False,
            returncode=124,
            stderr=f"dirval timed out after {timeout}s",
            stdout="",
        )
    except FileNotFoundError:
        return ValidationResult(
            subdir=subdir,
            ok=False,
            returncode=127,
            stderr=f"dirval not found (dirval-cmd: {dirval_cmd})",
            stdout="",
        )


def parallel_validate(
    subdirs: List[Path], dirval_cmd: str, workers: int, timeout: float
) -> List[ValidationResult]:
    results: List[ValidationResult] = []
    if not subdirs:
        return results

    print(
        f"Validating {len(subdirs)} directories with {workers} workers (dirval: {dirval_cmd})..."
    )
    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {
            pool.submit(run_dirval_validate, sd, dirval_cmd, timeout): sd
            for sd in subdirs
        }
        for fut in as_completed(future_map):
            res = fut.result()
            status = "ok" if res.ok else "error"
            print(f"[{status}] {res.subdir}")
            results.append(res)

    elapsed = time.time() - start
    print(f"Validation finished in {elapsed:.2f}s")
    return results


def print_dir_listing(path: Path, max_items: int = 50) -> None:
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except Exception as e:
        print(f"  (unable to list: {e})")
        return

    for i, entry in enumerate(entries):
        typ = "<DIR>" if entry.is_dir() else "     "
        print(f"  {typ} {entry.name}")
        if i + 1 >= max_items and len(entries) > i + 1:
            print(f"  ... (+{len(entries) - (i + 1)} more)")
            break


def confirm(prompt: str) -> bool:
    try:
        return input(prompt).strip().lower() in {"y", "yes"}
    except EOFError:
        return False


def delete_path(path: Path) -> Tuple[Path, bool, Optional[str]]:
    try:
        shutil.rmtree(path)
        return path, True, None
    except Exception as e:
        return path, False, str(e)


def process_deletions(failures: List[ValidationResult], assume_yes: bool) -> int:
    deleted_count = 0
    for res in failures:
        print("\n" + "=" * 80)
        print(f"Validation failed for: {res.subdir}")
        if res.stderr:
            print(f"stderr: {res.stderr}")
        if res.stdout:
            print(f"stdout: {res.stdout}")
        print("Contents:")
        print_dir_listing(res.subdir)

        should_delete = assume_yes or confirm("Delete this subdirectory? [y/N]: ")
        if not should_delete:
            continue

        print(f"Deleting: {res.subdir}")
        path, ok, err = delete_path(res.subdir)
        if ok:
            print(f"Deleted: {path}")
            deleted_count += 1
        else:
            print(f"Failed to delete {path}: {err}")

    return deleted_count


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate (and optionally delete) failed backup subdirectories in parallel using dirval."
    )

    parser.add_argument(
        "--backups-root",
        required=True,
        type=Path,
        help="Root directory containing backup folders (required).",
    )

    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--id", dest="backup_id", help="Backup folder name under backups root."
    )
    scope.add_argument(
        "--all",
        dest="all_mode",
        action="store_true",
        help="Scan all backups root/* folders.",
    )

    parser.add_argument(
        "--dirval-cmd",
        default="dirval",
        help="dirval executable/command to run (default: 'dirval').",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(2, multiprocessing.cpu_count()),
        help="Number of parallel validator workers (default: CPU count).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Per-directory dirval timeout in seconds (supports floats; default: 300).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Do not prompt; delete failing directories automatically.",
    )
    parser.add_argument(
        "--force-keep",
        type=int,
        default=0,
        help="In --all mode: keep (skip) the last N backup folders under --backups-root (default: 0).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        subdirs = discover_target_subdirs(
            args.backups_root,
            args.backup_id,
            bool(args.all_mode),
            int(args.force_keep),
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not subdirs:
        print("No subdirectories to validate. Nothing to do.")
        return 0

    results = parallel_validate(subdirs, args.dirval_cmd, args.workers, args.timeout)
    failures = [r for r in results if not r.ok]

    if not failures:
        print("\nAll directories validated successfully. No action required.")
        return 0

    print(f"\n{len(failures)} directory(ies) failed validation.")
    deleted = process_deletions(failures, assume_yes=args.yes)
    kept = len(failures) - deleted
    print(
        f"\nSummary: deleted={deleted}, kept={kept}, ok={len(results) - len(failures)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
