"""Client for Derpibooru API (Philomena)."""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .config import DEFAULT_DELAY


class DerpiClient:
    """Client for Derpibooru API."""

    BASE_URL = "https://derpibooru.org/api/v1/json"
    CDN_BASE = "https://derpicdn.net"
    USER_AGENT = "DerpiCLI/1.0"

    def __init__(
        self,
        api_key: Optional[str] = None,
        delay: float = DEFAULT_DELAY,
        filter_id: Optional[int] = None,
    ):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self.api_key = api_key
        self.delay = delay
        self.filter_id = filter_id
        self._last_request = 0.0

    # ---------- Inner methods ----------

    def _throttle(self) -> None:
        """Delay between API-requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET with throtling, key and handling 429."""
        self._throttle()

        if self.api_key:
            params["key"] = self.api_key
        if self.filter_id is not None and "filter_id" not in params:
            params["filter_id"] = self.filter_id

        url = f"{self.BASE_URL}/{endpoint}"
        resp = self.session.get(url, params=params, timeout=30)

        if resp.status_code == 429:
            wait = 10
            print(f"Warn: Rate limit. Waiting {wait} seconds...", file=sys.stderr)
            time.sleep(wait)
            return self._get(endpoint, params)

        resp.raise_for_status()
        return resp.json()

    # ---------- API-methods ----------

    def search(
        self,
        tags: str,
        page: int = 1,
        per_page: int = 50,
        sort_field: str = "created_at",
        sort_dir: str = "desc",
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        min_faves: Optional[int] = None,
        min_upvotes: Optional[int] = None,
        min_wilson: Optional[float] = None,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        uploader: Optional[str] = None,
        gallery: Optional[int] = None,
        faved_by: Optional[str] = None,
        upvoted_by: Optional[str] = None,
        watched: bool = False,
        min_tag_count: Optional[int] = None,
        max_tag_count: Optional[int] = None,
        first_seen_after: Optional[str] = None,
        first_seen_before: Optional[str] = None,
        created_at_after: Optional[str] = None,
        created_at_before: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search images with extended filters list."""
        params: Dict[str, Any] = {
            "q": tags,
            "page": page,
            "per_page": min(per_page, 50),
            "sf": sort_field,
            "sd": sort_dir,
        }

        numeric = {
            "min_score": min_score,
            "max_score": max_score,
            "min_faves": min_faves,
            "min_upvotes": min_upvotes,
            "min_wilson": min_wilson,
            "min_width": min_width,
            "min_height": min_height,
            "max_width": max_width,
            "max_height": max_height,
            "min_tag_count": min_tag_count,
            "max_tag_count": max_tag_count,
        }
        for key, value in numeric.items():
            if value is not None:
                params[key] = value

        if uploader:
            params["uploader"] = uploader
        if faved_by:
            params["faved_by"] = faved_by
        if upvoted_by:
            params["upvoted_by"] = upvoted_by
        if gallery is not None:
            params["gallery_id"] = gallery
        if watched:
            params["watched"] = "true"

        if first_seen_after:
            params["first_seen_at.gte"] = first_seen_after
        if first_seen_before:
            params["first_seen_at.lte"] = first_seen_before
        if created_at_after:
            params["created_at.gte"] = created_at_after
        if created_at_before:
            params["created_at.lte"] = created_at_before

        return self._get("search/images", params)

    def get_image(self, image_id: int) -> Dict[str, Any]:
        """Single image by ID."""
        return self._get(f"images/{image_id}", {})

    def get_random(self, tags: str = "") -> Dict[str, Any]:
        """Random image."""
        result = self.search(
            tags=tags or "*",
            page=1,
            per_page=1,
            sort_field="random",
            sort_dir="desc",
        )
        images = result.get("images", [])
        if not images:
         return {}
        return {"image": images[0]}

    def get_tags(self, names: List[str]) -> Dict[str, Any]:
        """Info about tags."""
        tags_info = []
        for name in names:
            result = self.search(tags=name, page=1, per_page=1)
            tags_info.append({
                "name": name,
                "images": result.get("total", 0),
                "category": "-",
                "description": "-",
            })
        return {"tags": tags_info}

    # ---------- Utilities ----------

    @staticmethod
    def pick_url(image: Dict[str, Any], representation: str = "full") -> Optional[str]:
        """Choose image URL with needed size."""
        reps = image.get("representations", {}) or {}
        for rep in [representation, "full", "large", "medium", "small", "thumb"]:
            if rep in reps and reps[rep]:
                return reps[rep]
        return None

    def download_image(
        self,
        image: Dict[str, Any],
        out_dir: Path,
        representation: str = "full",
    ) -> Optional[Path]:
        """Download image. Returns path or None."""
        url = self.pick_url(image, representation)
        if not url:
            return None

        clean_url = url.split("?")[0]
        ext = os.path.splitext(clean_url)[1] or ".png"
        fname = out_dir / f"{image['id']}{ext}"

        if fname.exists():
            return fname

        # Downloads from derpicdn.net - not consuming API limits
        resp = self.session.get(url, stream=True, timeout=60)
        resp.raise_for_status()

        with open(fname, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

        return fname