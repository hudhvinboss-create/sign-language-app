"""
Lightweight Text -> Sign asset loader.

Text -> Sign must display a shipped sign asset when one exists. It never
creates a fake hand, brick, placeholder drawing, or generated reference card.
"""

import os
from functools import lru_cache

from PIL import Image


class SignImageGenerator:
    def __init__(self, width=400, height=300):
        self.width = width
        self.height = height
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.asset_root = os.path.join(self.project_root, "assets")
        self.sign_asset_dir = os.path.join(self.asset_root, "signs")
        self.phrase_asset_dir = os.path.join(self.asset_root, "phrases")
        self.alphabet_asset_dir = os.path.join(self.asset_root, "alphabet")
        self.number_asset_dir = os.path.join(self.asset_root, "numbers")

    def _names(self, word):
        value = str(word or "").strip().lower()
        value = value.replace("'", "").replace("’", "")
        if not value:
            return []

        # Keep both naming conventions. The asset pack contains normalized
        # underscore names, while some older phrase/sign files use hyphens.
        names = [value, value.replace(" ", "_"), value.replace(" ", "-"),
                 value.replace("-", "_"), value.replace("-", "")]
        result = []
        seen = set()
        for name in names:
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result

    def _candidate_paths(self, word, image_path=None):
        """Return candidates with dedicated asset types taking priority."""
        candidates = []
        value = str(word or "").strip().lower().replace("'", "").replace("’", "")
        names = self._names(word)

        # Dedicated alphabet/number assets must win over generic sign files.
        # This prevents an older generic single-character asset from masking
        # the dedicated A-Z / 0-9 reference asset.
        if len(value) == 1 and value.isalpha():
            for name in names:
                candidates.append(os.path.join(self.alphabet_asset_dir, f"{name}.png"))

        if value.isdigit():
            for name in names:
                candidates.append(os.path.join(self.number_asset_dir, f"{name}.png"))

        # Phrase assets next, then the general sign library.
        for name in names:
            candidates.append(os.path.join(self.phrase_asset_dir, f"{name}.png"))
        for name in names:
            candidates.append(os.path.join(self.sign_asset_dir, f"{name}.png"))

        # An explicit database image is only a final fallback.
        if image_path:
            if os.path.isabs(image_path):
                candidates.append(image_path)
            else:
                candidates.append(os.path.join(self.project_root, image_path))

        result = []
        seen = set()
        for path in candidates:
            normalized = os.path.normcase(os.path.normpath(path))
            if normalized not in seen:
                seen.add(normalized)
                result.append(path)
        return result

    @lru_cache(maxsize=256)
    def _load_asset(self, path):
        if not path or not os.path.isfile(path):
            return None
        try:
            with Image.open(path) as source:
                return source.convert("RGB").copy()
        except (OSError, ValueError):
            return None

    def find_asset(self, word, image_path=None):
        for path in self._candidate_paths(word, image_path):
            if os.path.isfile(path):
                return path
        return None

    def generate(self, word, hand_position="", movement="", meaning="", image_path=None):
        """Load an existing asset. Never generate a fake visual."""
        asset_path = self.find_asset(word, image_path)
        if not asset_path:
            # Return a transparent/neutral image rather than inventing a sign.
            return Image.new("RGB", (self.width, self.height), (15, 15, 26))

        image = self._load_asset(asset_path)
        if image is None:
            return Image.new("RGB", (self.width, self.height), (15, 15, 26))
        return self._fit_image(image)

    def _fit_image(self, image):
        image = image.copy()
        image.thumbnail((self.width - 16, self.height - 16), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (self.width, self.height), (15, 15, 26))
        x = (self.width - image.width) // 2
        y = (self.height - image.height) // 2
        canvas.paste(image, (x, y))
        return canvas
