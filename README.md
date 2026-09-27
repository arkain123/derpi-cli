# derpi-cli

A command-line tool for the [Derpibooru](https://derpibooru.org) API —
search, filter, browse, and download artwork from your terminal.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Features

- **Search** images by any tag combination supported by Derpibooru.
- **Filter** by score, faves, upvotes, Wilson score, dimensions, tag count,
  uploader, gallery, date range, and more.
- **Download** results with automatic pagination and de-duplication.
- **Random** image picker for a given tag set.
- **Tag statistics** — number of images per tag.
- **Respects rate limits** — automatic throttling and HTTP 429 handling.
- **Config file** in `~/.config/derpi-cli/config.json` with mode `0600`.
- **JSON output** for scripting and piping into `jq`.
- **Zero dependencies** beyond `requests`.

---

## Installation

### One-liner (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/arkain123/derpi-cli/main/install.sh | bash
```

With an API key saved to config:

```bash
curl -fsSL https://raw.githubusercontent.com/arkain123/derpi-cli/main/install.sh \
    | bash -s -- --key YOUR_API_KEY
```

The installer:

1. Checks for Python 3.9+.
2. Installs [`pipx`](https://pipx.pypa.io) if missing.
3. Clones the repository to `~/.local/share/derpi-cli`.
4. Installs the package with `pipx install -e`.
5. Ensures `~/.local/bin` is in `PATH`.
6. Creates a default config file.

### Manual installation with pipx

```bash
git clone https://github.com/arkain123/derpi-cli.git
cd derpi-cli
pipx install -e .
```

### Manual installation with pip

```bash
git clone https://github.com/arkain123/derpi-cli.git
cd derpi-cli
pip install --user -e .
```

Make sure `~/.local/bin` is in your `PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### From source (development)

```bash
git clone https://github.com/you/derpi-cli.git
cd derpi-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Uninstall

```bash
./install.sh --uninstall
```

Or manually:

```bash
pipx uninstall derpi-cli
rm -rf ~/.local/share/derpi-cli
```

---

## Quick start

```bash
# Search for safe Fluttershy images
derpi search "fluttershy, safe"

# Download 20 of them
derpi download "fluttershy, safe" --limit 20

# Random Pinkie Pie image
derpi random "pinkie pie, safe"

# Details for a specific image
derpi info 123456

# Tag statistics
derpi tags fluttershy
```

---

## Configuration

On first run, `derpi` creates `~/.config/derpi-cli/config.json` with mode `0600`:

```json
{
  "api_key": "",
  "rate_limit_delay": 0.5,
  "default_filter_id": null,
  "default_output_dir": "~/Downloads"
}
```

| Field | Description |
|---|---|
| `api_key` | Your Derpibooru API key. Enables personal filters and watchlist. |
| `rate_limit_delay` | Seconds between API requests. Default `0.5` (20 req / 10 s). |
| `default_filter_id` | Filter ID to apply to all searches. `null` disables it. |
| `default_output_dir` | Default download directory. `~` is expanded. |

### Getting an API key

1. Log in to [derpibooru.org](https://derpibooru.org).
2. Open your account page.
3. Copy the API key and paste it into the config file.

The API key is treated as a password. Never commit it to a public repository.

---

## Commands

### `derpi search TAGS`

Search for images and print a summary.

```bash
derpi search "fluttershy, safe"
derpi search "rarity, safe" --sort score --per-page 10
derpi search "twilight sparkle, safe" --json | jq '.images[].id'
```

Output includes ID, score, faves, Wilson score, dimensions, MIME type,
first few tags, and a preview URL.

### `derpi download TAGS`

Download images matching the given tags.

```bash
derpi download "fluttershy, safe" --limit 20
derpi download "wallpaper, safe" --min-width 1920 --min-height 1080 -o ~/Pictures
derpi download "rarity, safe" --size large --min-score 100 --limit 50
```

Downloads go through the CDN at `derpicdn.net` and do not consume the API
rate limit.

### `derpi info ID`

Show full metadata for a single image.

```bash
derpi info 123456
derpi info 123456 --json
```

### `derpi random [TAGS]`

Fetch a random image matching the tags (or any image if no tags are given).

```bash
derpi random "pinkie pie, safe"
derpi random "rarity, safe, score.gt:100"
```

### `derpi tags NAME [NAME ...]`

Show the number of images for each tag.

```bash
derpi tags fluttershy
derpi tags fluttershy "rainbow dash" rarity
```

### `derpi --config`

Print the path to the config file and exit.

```bash
derpi --config
```

### `derpi --version`

Print the version and exit.

---

## Options

### Search and download

| Option | Description |
|---|---|
| `--page N` | Page number (default: `1`). |
| `--per-page N` | Results per page, 1–50 (default: `50`). |
| `--sort FIELD` | Sort field: `created_at`, `score`, `faves`, `wilson_score`, `random`, `updated_at`, `tag_count`, `width`, `height`, `first_seen_at`. |
| `--dir DIRECTION` | Sort direction: `desc` or `asc` (default: `desc`). |
| `--min-score N` | Minimum score. |
| `--max-score N` | Maximum score. |
| `--min-faves N` | Minimum number of faves. |
| `--min-upvotes N` | Minimum number of upvotes. |
| `--min-wilson F` | Minimum Wilson score (0.0–1.0). |
| `--min-width N` | Minimum width in pixels. |
| `--min-height N` | Minimum height in pixels. |
| `--max-width N` | Maximum width in pixels. |
| `--max-height N` | Maximum height in pixels. |
| `--uploader NAME` | Filter by uploader. |
| `--gallery ID` | Filter by gallery ID. |
| `--faved-by NAME` | Images faved by the given user. |
| `--upvoted-by NAME` | Images upvoted by the given user. |
| `--watched` | Only images from your watchlist (requires API key). |
| `--min-tag-count N` | Minimum number of tags. |
| `--max-tag-count N` | Maximum number of tags. |
| `--first-seen-after DATE` | First seen after date (`YYYY-MM-DD`). |
| `--first-seen-before DATE` | First seen before date (`YYYY-MM-DD`). |
| `--created-at-after DATE` | Uploaded after date (`YYYY-MM-DD`). |
| `--created-at-before DATE` | Uploaded before date (`YYYY-MM-DD`). |

### `search` only

| Option | Description |
|---|---|
| `--json` | Output raw JSON. |

### `download` only

| Option | Description |
|---|---|
| `-o, --output DIR` | Output directory (overrides config). |
| `--limit N` | Maximum number of files to download (default: `50`). |
| `--size SIZE` | Image size: `full`, `large`, `medium`, `small`, `thumb` (default: `full`). |

### `info` and `random` only

| Option | Description |
|---|---|
| `--json` | Output raw JSON. |

### `tags` only

| Option | Description |
|---|---|
| `--json` | Output raw JSON. |

---

## Examples

### Top-rated safe Fluttershy images

```bash
derpi search "fluttershy, safe" --sort score --per-page 10
```

### Download high-resolution wallpapers

```bash
derpi download "wallpaper, safe" \
    --min-width 1920 --min-height 1080 \
    --min-score 100 \
    --limit 30 \
    -o ~/Pictures/wallpapers
```

### Images faved by a specific user

```bash
derpi search "safe, --faved-by:someuser" --min-score 50
```

### Watchlist (requires API key)

```bash
derpi search "my:watched" --watched --sort wilson_score
```

### Random high-score image

```bash
derpi random "rarity, safe, score.gt:100"
```

### Pipe IDs into another tool

```bash
derpi search "fluttershy, safe" --json | jq -r '.images[].id' | head -10
```

### Tag statistics

```bash
derpi tags fluttershy "rainbow dash" rarity
```

### Only images uploaded in the last month

```bash
derpi search "safe, oc" --created-at-after 2026-08-27 --sort created_at
```

---

## Rate limits

Derpibooru allows **20 requests per 10 seconds**. `derpi` handles this
automatically:

- A pause of `rate_limit_delay` seconds is inserted between API requests
  (default `0.5 s` = exactly 20 req / 10 s).
- On HTTP `429 Too Many Requests`, the client waits 10 seconds and retries.
- File downloads go through `derpicdn.net`, which is a separate service and
  does not count against the API limit.

If you plan to run large downloads, consider increasing `rate_limit_delay` in
the config file to be safe.

---

## File layout

```
~/.config/derpi-cli/config.json    # config (mode 0600)
~/.local/bin/derpi                 # executable
~/.local/share/derpi-cli/          # sources (if installed via install.sh)
~/Downloads/                       # default output directory
```

---

## Man page

A man page is included in the repository (`derpi.1`). Install it with:

```bash
sudo cp derpi.1 /usr/local/share/man/man1/
sudo mandb
man derpi
```

Or for a user-local install:

```bash
mkdir -p ~/.local/share/man/man1
cp derpi.1 ~/.local/share/man/man1/
echo 'export MANPATH="$HOME/.local/share/man:$MANPATH"' >> ~/.bashrc
source ~/.bashrc
man derpi
```

---

## Development

### Project structure

```
derpi-cli/
├── derpi/
│   ├── __init__.py       # version, metadata
│   ├── config.py         # config file handling
│   ├── client.py         # API client
│   ├── commands.py       # CLI command implementations
│   └── cli.py            # argument parser and entry point
├── derpi.py              # direct entrypoint
├── derpi.1               # man page
├── install.sh            # installer
├── pyproject.toml        # packaging
├── requirements.txt
└── README.md
```

### Running from source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
derpi --help
```

### Running tests

```bash
pip install pytest
pytest
```

### Building a wheel

```bash
pip install build
python -m build
```

The resulting wheel and sdist will be in `dist/`.

---

## Troubleshooting

### `derpi: command not found`

`~/.local/bin` is probably not in your `PATH`. Add it:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### `Err: HTTP error: 429`

Rate limit hit. Increase `rate_limit_delay` in the config file:

```json
"rate_limit_delay": 1.0
```

### `Err: HTTP error: 400 Bad Request` on `random`

Make sure you are using a recent version. Older releases used the deprecated
`/images/random` endpoint, which has been removed from the Philomena API.

### Files downloaded into a literal `~/` directory

Update `derpi` to version 2.0.1+ — it uses `Path.expanduser().resolve()` to
handle `~` in paths correctly.

### Wrong number of images in `tags`

The `tags` command uses the search API to count images. The number may differ
slightly from the website because of hidden or filtered content.

---

## License

MIT — see [LICENSE](LICENSE) for details.

## Contributing

Pull requests are welcome. Please open an issue first for larger changes.

## See also

- [Derpibooru API documentation](https://derpibooru.org/pages/api)
- [Philomena project](https://github.com/philomena-dev/philomena)
- [`pipx`](https://pipx.pypa.io) — Python CLI package installer
