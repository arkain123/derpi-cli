"""Args parser and entry point."""

import argparse
import sys

import requests

from . import __version__
from .client import DerpiClient
from .commands import cmd_download, cmd_info, cmd_random, cmd_search, cmd_tags
from .config import CONFIG_FILE, DEFAULT_DELAY, load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="derpi",
        description="CLI for Derpibooru API: search, view and download arts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  derpi search "fluttershy, safe" --min-score 100
  derpi search "rarity, safe" --sort score --json
  derpi download "fluttershy, safe" -o ./arts --limit 20 --min-faves 50
  derpi download "twilight sparkle" --size large --min-wilson 0.9
  derpi info 123456
  derpi random "pinkie pie, safe"
  derpi tags "fluttershy" "rainbow dash"
        """,
    )

    parser.add_argument("--version", action="version",
                        version=f"derpi {__version__}")
    parser.add_argument("--config", action="store_true",
                        help="Show path for config")

    sub = parser.add_subparsers(dest="command", help="Commands")

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("tags", help="Tags (For ex.: 'fluttershy, safe')")
        p.add_argument("--page", type=int, default=1,
                       help="Page number (default: 1)")
        p.add_argument("--per-page", type=int, default=50,
                       choices=range(1, 51), metavar="1-50",
                       help="Results on page (default: 50)")
        p.add_argument("--sort", default="created_at",
                       choices=["created_at", "score", "faves", "wilson_score",
                                "random", "updated_at", "tag_count",
                                "width", "height", "first_seen_at"],
                       help="Sort (default: created_at)")
        p.add_argument("--dir", default="desc", choices=["desc", "asc"],
                       help="Search direction (default: desc)")
        p.add_argument("--min-score", type=int, help="Min. score")
        p.add_argument("--max-score", type=int, help="Max. score")
        p.add_argument("--min-faves", type=int, help="Min. faves")
        p.add_argument("--min-upvotes", type=int, help="Min. upvotes")
        p.add_argument("--min-wilson", type=float, help="Min. Wilson score")
        p.add_argument("--min-width", type=int, help="Min. width (px)")
        p.add_argument("--min-height", type=int, help="Min. height (px)")
        p.add_argument("--max-width", type=int, help="Max. width (px)")
        p.add_argument("--max-height", type=int, help="Max. height (px)")
        p.add_argument("--uploader", type=str, help="Filter by uploader")
        p.add_argument("--gallery", type=int, help="Gallery ID")
        p.add_argument("--faved-by", type=str, help="User favorites")
        p.add_argument("--upvoted-by", type=str, help="User upvotes")
        p.add_argument("--watched", action="store_true",
                       help="Only from watchlist (key needed)")
        p.add_argument("--min-tag-count", type=int, help="Min. tags amount")
        p.add_argument("--max-tag-count", type=int, help="Max. tags amount")
        p.add_argument("--first-seen-after", type=str,
                       help="First seen after (YYYY-MM-DD)")
        p.add_argument("--first-seen-before", type=str,
                       help="First seen before (YYYY-MM-DD)")
        p.add_argument("--created-at-after", type=str,
                       help="Created after (YYYY-MM-DD)")
        p.add_argument("--created-at-before", type=str,
                       help="Created before (YYYY-MM-DD)")

    # search
    p_search = sub.add_parser("search", help="Search images")
    add_common(p_search)
    p_search.add_argument("--json", action="store_true", help="Output in JSON")

    # download
    p_down = sub.add_parser("download", help="Download by tags")
    add_common(p_down)
    p_down.add_argument("-o", "--output", help="Directory (default from config)")
    p_down.add_argument("--limit", type=int, default=50,
                        help="Amount to download (default: 50)")
    p_down.add_argument("--size", default="full",
                        choices=["full", "large", "medium", "small", "thumb"],
                        help="Size (default: full)")

    # info
    p_info = sub.add_parser("info", help="Image info by ID")
    p_info.add_argument("image_id", type=int, help="Image ID")
    p_info.add_argument("--json", action="store_true", help="Output in JSON")

    # random
    p_rand = sub.add_parser("random", help="Random image by tags")
    p_rand.add_argument("tags", nargs="?", default="", help="Tags (optional)")
    p_rand.add_argument("--json", action="store_true", help="Output in JSON")

    # tags
    p_tags = sub.add_parser("tags", help="Tags info")
    p_tags.add_argument("names", nargs="+", help="Tags separated by space")
    p_tags.add_argument("--json", action="store_true", help="Output in JSON")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Show config path
    if args.config:
        print(f"Config: {CONFIG_FILE}")
        print("Exists." if CONFIG_FILE.exists()
              else "Not created. Run any command for creation.")
        return 0

    if not args.command:
        parser.print_help()
        return 1

    # Config (Creates interactively at first run)
    cfg = load_config(create_if_missing=True)

    if not cfg.get("api_key"):
        print("   API-key not specified. Watchlist and personal filters unavailable.",
              file=sys.stderr)
        print(f"   Change {CONFIG_FILE}.", file=sys.stderr)

    client = DerpiClient(
        api_key=cfg.get("api_key") or None,
        delay=cfg.get("rate_limit_delay", DEFAULT_DELAY),
        filter_id=cfg.get("default_filter_id"),
    )

    try:
        if args.command == "search":
            cmd_search(client, args)
        elif args.command == "download":
            cmd_download(client, args, cfg)
        elif args.command == "info":
            cmd_info(client, args)
        elif args.command == "random":
            cmd_random(client, args)
        elif args.command == "tags":
            cmd_tags(client, args)
    except requests.HTTPError as e:
        print(f"Err: HTTP error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"     Response: {e.response.text[:500]}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n     Canceled by user.", file=sys.stderr)
        return 130

    return 0