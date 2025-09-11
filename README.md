# Cleanup Failed Backups (cleanback) 🚮⚡

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach)
[![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)

**Repository:** https://github.com/kevinveenbirkenbach/cleanup-failed-backups

This tool validates and (optionally) cleans up **failed Docker backup directories**.  
It scans backup folders under `/Backups`, uses [`dirval`](https://github.com/kevinveenbirkenbach/directory-validator) to validate each subdirectory, and lets you delete the ones that fail validation. Validation runs **in parallel** for performance; deletions are controlled and can be interactive or automatic.

---

## ✨ Highlights

- **Parallel validation** of backup subdirectories
- Uses **`dirval`** (`directory-validator`) via CLI for robust validation
- **Interactive** or **non-interactive** deletion flow (`--yes`)
- Supports validating a single backup **ID** or **all** backups

---

## 📦 Installation

This project is installable via **pkgmgr** (Kevin’s package manager).

**New pkgmgr alias:** `cleanback`

```bash
# Install pkgmgr first (if you don't have it):
# https://github.com/kevinveenbirkenbach/package-manager

pkgmgr install cleanback
````

> `dirval` is declared as a dependency (see `requirements.yml`) and will be resolved by pkgmgr.

---

## 🔧 Requirements

* Python 3.8+
* `dirval` available on PATH (resolved automatically by `pkgmgr install cleanback`)
* Access to `/Backups` directory tree

---

## 🚀 Usage

The executable is `main.py`:

```bash
# Validate a single backup ID (under /Backups/<ID>/backup-docker-to-local)
python3 main.py --id <ID>

# Validate ALL backup IDs under /Backups/*/backup-docker-to-local
python3 main.py --all
```

### Common options

* `--dirval-cmd <path-or-name>` — command to run `dirval` (default: `dirval`)
* `--workers <int>` — parallel workers (default: CPU count, min 2)
* `--timeout <seconds>` — per-directory validation timeout (float supported; default: 300.0)
* `--yes` — **non-interactive**: auto-delete directories that fail validation

### Examples

```bash
# Validate a single backup and prompt for deletions on failures
python3 main.py --id 2024-09-01T12-00-00

# Validate everything with 8 workers and auto-delete failures
python3 main.py --all --workers 8 --yes

# Use a custom dirval binary and shorter timeout
python3 main.py --all --dirval-cmd /usr/local/bin/dirval --timeout 5.0
```

---

## 🧪 Tests

```bash
make test
```

This runs the unit tests in `test.py`. Tests create a temporary `/Backups`-like tree and a fake `dirval` to simulate success/failure/timeout behavior.

---

## 📁 Project Layout

* `main.py` — CLI entry point (parallel validator + cleanup)
* `test.py` — unit tests
* `requirements.yml` — `pkgmgr` dependencies (includes `dirval`)
* `Makefile` — `make test` and an informational `make install`

---

## 🪪 License

This project is licensed under the **GNU Affero General Public License v3.0**.
See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Kevin Veen-Birkenbach**
🌐 [https://www.veen.world](https://www.veen.world)
📧 [kevin@veen.world](mailto:kevin@veen.world)
