"""CLI commands realization."""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from .client import DerpiClient
from .config import DEFAULT_OUTPUT


# ---------- Search ----------

def cmd_search(client: DerpiClient, args) -> None:
    """Search and printing results."""
    result = client.search(
        tags=args.tags,
        page=args.page,
        per_page=args.per_page,
        sort_field=args.sort,
        sort_dir=args.dir,
        min_score=args.min_score,
        max_score=args.max_score,
        min_faves=args.min_faves,
        min_upvotes=args.min_upvotes,
        min_wilson=args.min_wilson,
        min_width=args.min_width,
        min_height=args.min_height,
        max_width=args.max_width,
        max_height=args.max_height,
        uploader=args.uploader,
        gallery=args.gallery,
        faved_by=args.faved_by,
        upvoted_by=args.upvoted_by,
        watched=args.watched,
        min_tag_count=args.min_tag_count,
        max_tag_count=args.max_tag_count,
        first_seen_after=args.first_seen_after,
        first_seen_before=args.first_seen_before,
        created_at_after=args.created_at_after,
        created_at_before=args.created_at_before,
    )

    images = result.get("images", [])
    total = result.get("total", 0)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"Found: {total} | Page {args.page} | Shows: {len(images)}\n")

    for img in images:
        url = (DerpiClient.pick_url(img, "large")
               or DerpiClient.pick_url(img, "thumb") or "—")
        print(f"  ID: {img['id']}")
        print(f"  Score: {img.get('score', 0)} | "
              f"Faves: {img.get('faves', 0)} | "
              f"Wilson: {img.get('wilson_score', 0):.3f}")
        print(f"  Size: {img.get('width', '?')}x{img.get('height', '?')} | "
              f"{img.get('mime_type', '—')}")
        tags = img.get("tags", [])
        shown = ", ".join(tags[:8])
        if len(tags) > 8:
            shown += "..."
        print(f"  Tags: {shown}")
        print(f"  URL:  {url}")
        print()


# ---------- Download ----------

def cmd_download(client: DerpiClient, args, config: Dict[str, Any]) -> None:
    """Download search result."""
    raw_out = args.output or config.get("default_output_dir", DEFAULT_OUTPUT)
    out_dir = Path(raw_out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    page = 1
    downloaded = 0
    total_limit = args.limit or float("inf")
    seen_ids = set()

    while downloaded < total_limit:
        remaining = int(total_limit - downloaded) if total_limit != float("inf") else None
        per_page = min(args.per_page, remaining) if remaining else args.per_page

        result = client.search(
            tags=args.tags,
            page=page,
            per_page=per_page,
            sort_field=args.sort,
            sort_dir=args.dir,
            min_score=args.min_score,
            max_score=args.max_score,
            min_faves=args.min_faves,
            min_upvotes=args.min_upvotes,
            min_wilson=args.min_wilson,
            min_width=args.min_width,
            min_height=args.min_height,
            max_width=args.max_width,
            max_height=args.max_height,
            uploader=args.uploader,
            gallery=args.gallery,
            faved_by=args.faved_by,
            upvoted_by=args.upvoted_by,
            watched=args.watched,
            min_tag_count=args.min_tag_count,
            max_tag_count=args.max_tag_count,
            first_seen_after=args.first_seen_after,
            first_seen_before=args.first_seen_before,
            created_at_after=args.created_at_after,
            created_at_before=args.created_at_before,
        )

        images = result.get("images", [])
        if not images:
            break

        total = result.get("total", 0)
        print(f"Page {page} | Total: {total} | On page: {len(images)}")

        for img in images:
            if downloaded >= total_limit:
                break
            if img["id"] in seen_ids:
                continue
            seen_ids.add(img["id"])

            path = client.download_image(img, out_dir, args.size)
            if path:
                downloaded += 1
                print(f"  V [{downloaded}] {path.name}")
            else:
                print(f"  X ID {img['id']} - No URL", file=sys.stderr)

        page += 1
        if len(images) < per_page:
            break

    print(f"\nDownloaded: {downloaded} -> {out_dir}")


# ---------- info ----------

def cmd_info(client: DerpiClient, args) -> None:
    """Image details."""
    result = client.get_image(args.image_id)
    img = result.get("image", result)

    if args.json:
        print(json.dumps(img, indent=2, ensure_ascii=False))
        return

    print(f"ID:          {img.get('id')}")
    print(f"Score:       {img.get('score', 0)}  "
          f"(up: {img.get('upvotes', 0)}, down: {img.get('downvotes', 0)})")
    print(f"Faves:       {img.get('faves', 0)}")
    print(f"Wilson:      {img.get('wilson_score', 0):.4f}")
    print(f"Uploaded:    {img.get('created_at', '—')}")
    print(f"First seen:  {img.get('first_seen_at', '—')}")
    print(f"Size:        {img.get('width', '?')}x{img.get('height', '?')} "
          f"({img.get('size', '?')} bytes)")
    print(f"MIME:        {img.get('mime_type', '—')}")
    print(f"Duration:    {img.get('duration', '—')}")
    print(f"Uploader:    {img.get('uploader', '—')}")
    sources = img.get("source_urls", []) or []
    print(f"Source:      {', '.join(sources) or '—'}")
    print(f"Tags ({img.get('tag_count', 0)}): {', '.join(img.get('tags', []))}")
    print()
    print("Representations:")
    reps = img.get("representations", {}) or {}
    for name in ["full", "large", "medium", "small", "tall",
                 "thumb", "thumb_small", "thumb_tiny"]:
        if name in reps and reps[name]:
            print(f"  {name:12} {reps[name]}")


# ---------- Random ----------

def cmd_random(client: DerpiClient, args) -> None:
    """Random image by tags."""
    result = client.get_random(args.tags or "")
    img = result.get("image", result)

    if args.json:
        print(json.dumps(img, indent=2, ensure_ascii=False))
        return

    url = DerpiClient.pick_url(img, "large")
    print(f"ID: {img.get('id')}")
    print(f"   {url}")


# ---------- Tags ----------

def cmd_tags(client: DerpiClient, args) -> None:
    """Tags info (images quantity)."""
    result = client.get_tags(args.names)
    tags = result.get("tags", [])

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    for tag in tags:
        print(f"   {tag.get('name')}")
        print(f"   Images: {tag.get('images', '-')}")
        print()