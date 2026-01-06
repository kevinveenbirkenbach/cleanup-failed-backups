# Cleanup Failed Backups (cleanback) 🚮⚡

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach)
[![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)

**Repository:** https://github.com/kevinveenbirkenbach/cleanup-failed-backups

`cleanback` validates and (optionally) cleans up **failed Docker backup directories** in a **production-safe** way.

It scans backup folders under a configurable backups root (for example `/Backups`), uses `dirval` to validate each backup subdirectory, and removes **only those backups that are confirmed to be invalid**.

Validation runs **in parallel** for performance; deletions are **explicitly controlled** and can be interactive or fully automated.

---

## ✨ Highlights

- **Parallel validation** of backup subdirectories
- Uses **`dirval`** (directory validator) via CLI
- **Safe deletion model**: only truly invalid backups are removed
- **Interactive** or **non-interactive** cleanup (`--yes`)
- Supports validating a single backup **ID** or **all** backups
- Clear **exit code semantics** for CI and system services
- Clean **Python package** with `pyproject.toml`
- **Unit tests** and **Docker-based E2E tests**

---

## 📦 Installation

### Via pip (recommended)

```bash
pip install cleanback
```

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
* Read/write access to the backups root directory tree (e.g. `/Backups`)
* `dirval` (installed automatically via pip dependency)

---

## 🚀 Usage

### CLI entrypoint

After installation, the command is:

```bash
cleanback
```

---

### Validate a single backup ID

```bash
cleanback --backups-root /Backups --id <ID>
```

Validates directories under:

```
/Backups/<ID>/backup-docker-to-local/*
```

---

### Validate all backups

```bash
cleanback --backups-root /Backups --all
```

Scans:

```
/Backups/*/backup-docker-to-local/*
```

---

## ⚙️ Common options

| Option               | Description                                                                           |
| -------------------- | ------------------------------------------------------------------------------------- |
| `--dirval-cmd <cmd>` | Path or name of `dirval` executable (default: `dirval`)                               |
| `--workers <n>`      | Number of parallel validator workers (default: CPU count, minimum 2)                  |
| `--timeout <sec>`    | Per-directory validation timeout in seconds (float supported, default: `300.0`)       |
| `--yes`              | Non-interactive mode: automatically delete **invalid** backups (dirval rc=1 only)     |
| `--force-keep <n>`   | In `--all` mode: skip the last *n* timestamp subdirectories inside each backup folder |

> **Note:** Backups affected by timeouts or infrastructure errors are **never deleted automatically**, even when `--yes` is used.

---

## 🧪 Examples

```bash
# Validate a single backup and prompt before deleting invalid ones
cleanback --backups-root /Backups --id 2024-09-01T12-00-00
```

```bash
# Validate all backups and automatically delete invalid ones
cleanback --backups-root /Backups --all --workers 8 --yes
```

```bash
# Use a custom dirval binary and a short timeout (testing only)
cleanback \
  --backups-root /Backups \
  --all \
  --dirval-cmd /usr/local/bin/dirval \
  --timeout 5.0
```

---

## 🔒 Safety & Design Notes

* **Validation and deletion are strictly separated**
* Only backups explicitly marked **invalid by `dirval`** are eligible for deletion
* **Timeouts and infrastructure errors are NOT treated as invalid backups**
* Backups affected by timeouts are **never deleted automatically**
* Infrastructure problems (timeouts, missing `dirval`) cause a **non-zero exit code**
* Deletions require confirmation unless `--yes` is specified
* Tests never touch the host filesystem (E2E tests run inside Docker only)

This design makes `cleanback` safe for unattended operation on production systems.

---

## 🚦 Exit codes

`cleanback` uses exit codes to clearly distinguish between backup issues and infrastructure problems:

| Exit code | Meaning                                                            |
| --------- | ------------------------------------------------------------------ |
| `0`       | All backups valid, or invalid backups were successfully removed    |
| `1`       | Validation infrastructure problem (e.g. timeout, missing `dirval`) |
| `2`       | CLI usage or configuration error                                   |

This makes the tool suitable for **CI pipelines**, **systemd services**, and other automation.

---

## 🧪 Tests

Run all tests (unit + Docker-based E2E):

```bash
make test
```

---

## 🪪 License

This project is licensed under the **GNU Affero General Public License v3.0**.
See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Kevin Veen-Birkenbach**
🌐 [https://www.veen.world](https://www.veen.world)
📧 [kevin@veen.world](mailto:kevin@veen.world)
