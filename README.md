# Cleanup Failed Backups (cleanback) 🚮⚡

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach)
[![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)

**Repository:** https://github.com/kevinveenbirkenbach/cleanup-failed-backups

`cleanback` validates and (optionally) cleans up **failed Docker backup directories**.  
It scans backup folders under a configurable backups root (e.g. `/Backups`), uses `dirval` to validate each subdirectory, and lets you delete the ones that fail validation.

Validation runs **in parallel** for performance; deletions are controlled and can be **interactive** or **fully automatic**.

---

## ✨ Highlights

- **Parallel validation** of backup subdirectories
- Uses **`dirval`** (directory-validator) via CLI
- **Interactive** or **non-interactive** deletion flow (`--yes`)
- Supports validating a single backup **ID** or **all** backups
- Clean **Python package** with `pyproject.toml`
- **Unit + Docker-based E2E tests**

---

## 📦 Installation

### Via pip (recommended)

```bash
pip install cleanback
````

This installs:

* the `cleanback` CLI
* `dirval` as a dependency (declared in `pyproject.toml`)

### Editable install (for development)

```bash
git clone https://github.com/kevinveenbirkenbach/cleanup-failed-backups
cd cleanup-failed-backups
pip install -e .
```

---

## 🔧 Requirements

* Python **3.8+**
* Access to the backups root directory tree (e.g. `/Backups`)
* `dirval` (installed automatically via pip dependency)

---

## 🚀 Usage

### CLI entrypoint

After installation, the command is:

```bash
cleanback
```

### Validate a single backup ID

```bash
cleanback --backups-root /Backups --id <ID>
```

Validates directories under:

```
/Backups/<ID>/backup-docker-to-local/*
```

### Validate all backups

```bash
cleanback --backups-root /Backups --all
```

Scans:

```
/Backups/*/backup-docker-to-local/*
```

---

### Common options

| Option               | Description                                                        |
| -------------------- | ------------------------------------------------------------------ |
| `--dirval-cmd <cmd>` | Path or name of `dirval` executable (default: `dirval`)            |
| `--workers <n>`      | Parallel workers (default: CPU count, min 2)                       |
| `--timeout <sec>`    | Per-directory validation timeout (float supported, default: 300.0) |
| `--yes`              | Non-interactive mode: delete failures automatically                |

---

### Examples

```bash
# Validate a single backup and prompt on failures
cleanback --backups-root /Backups --id 2024-09-01T12-00-00

# Validate everything with 8 workers and auto-delete failures
cleanback --backups-root /Backups --all --workers 8 --yes

# Use a custom dirval binary and short timeout
cleanback --backups-root /Backups --all --dirval-cmd /usr/local/bin/dirval --timeout 5.0
```

---

## 🧪 Tests

### Run all tests

```bash
make test
```

---

## 🔒 Safety & Design Notes

* **No host filesystem is modified** during tests
  (E2E tests run exclusively inside Docker)
* Deletions are **explicitly confirmed** unless `--yes` is used
* Timeouts are treated as **validation failures**
* Validation and deletion phases are **clearly separated**

---

## 🪪 License

This project is licensed under the **GNU Affero General Public License v3.0**.
See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Kevin Veen-Birkenbach**
🌐 [https://www.veen.world](https://www.veen.world)
📧 [kevin@veen.world](mailto:kevin@veen.world)
