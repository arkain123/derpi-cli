# Changelog

## [2.0.1] - 2026-09-27

### Fixed
- `~` in output paths is now expanded correctly (previously created a
  literal `~` directory).
- `random` uses `sf=random` search instead of the removed `/images/random`
  endpoint.
- `tags` uses the search API to count images per tag.

## [2.0.0] - 2026-09-27

### Added
- Config file at `~/.config/derpi-cli/config.json`.
- Extended search filters (score, faves, dimensions, dates, uploader, etc.).
- `random` and `tags` commands.
- JSON output for scripting.
- One-line installer.
- Man page.

## [1.0.0] - 2026-09-27

### Added
- Initial release: `search`, `download`, `info` commands.
