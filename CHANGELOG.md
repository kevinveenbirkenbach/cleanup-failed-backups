## [1.3.0] - 2026-01-06

* Cleanup is now production-safe: only invalid backups are deleted; timeouts no longer trigger automatic removal.


## [1.2.1] - 2026-01-06

* Fixed: --force-keep now applies to timestamp subdirectories inside each backup-docker-to-local folder instead of skipping entire backup folders.


## [1.2.0] - 2025-12-31

* Adds a force keep N option to all mode to skip the most recent backups during cleanup, with Docker based E2E tests ensuring the latest backups are preserved.


## [1.1.0] - 2025-12-31

* The backups directory is now configurable via --backups-root instead of being hardcoded to /Backups.


## [1.0.0] - 2025-12-28

* Official Release 🥳

