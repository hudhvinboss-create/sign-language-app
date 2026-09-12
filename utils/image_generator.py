"""
Sign Language Reference Image Loader.

The Text -> Sign screen should display the real reference assets shipped with
this project. The old implementation drew a fake hand made from rectangles,
which produced the unwanted "brick" image and also did unnecessary drawing on
Every translation.

This module now:
- loads assets/signs/<sign>.png when available
- understands spaces and hyphens in sign names
- caches loaded images for fast navigation
- uses the database image_path when one is supplied
- provides a lightweight text-only fallback when an asset is missing
"""

import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont


class SignImageGenerator:
    def __init__(self, width=400, height=300):
        self.width = width
        self.height = height
        self.title_font = self._find_font(28, bold=True)
        self.body_font = self._find_font(15)
        self.small_font = self._find_font(12)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.sign_asset_dir = os.path.join(self.project_root, "assets", "signs")

    def _find_font(self, size, bold=False):
        names = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
        ]
        roots = [
            "/usr/share/fonts/truetype/dejavu",
            "/usr/share/fonts/TTF",
            "/usr/share/fonts/liberation",
        ]
        for root in roots:
            for name in names:
                path = os.path.join(root, name)
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except OSError:
                        pass
        return ImageFont.load_default()

    def _normalise_name(self, word):
        value = str(word or "").strip().lower()
        value = value.replace("'", "").replace("’", "")
        value = value.replace("-", "_").replace(" ", "_")
        return value

    def _candidate_paths(self, word, image_path=None):
        candidates = []

        if image_path:
            if os.path.isabs(image_path):
                candidates.append(image_path)
            else:
                candidates.append(os.path.join(self.project_root, image_path))

        name = self._normalise_name(word)
        if name:
            candidates.extend([
                os.path.join(self.sign_asset_dir, f"{name}.png"),
                os.path.join(self.project_root, "alphabet", f"{name}.png")
                if len(name) == 1 else "",
                os.path.join(self.project_root, "numbers", f"{name}.png")
                if name.isdigit() else "",
            ])

        return [path for path in candidates if path]

    @lru_cache(maxsize=256)
    def _load_asset(self, path):
        if not path or not os.path.isfile(path):
            return None
        try:
            with Image.open(path) as source:
                # Copy the image so the file handle can close immediately.
                return source.convert("RGB").copy()
        except (OSError, ValueError):
            return None

    def find_asset(self, word, image_path=None):
        """Return the first existing PNG asset for a sign, or None."""
        for path in self._candidate_paths(word, image_path):
            if os.path.isfile(path):
                return path
        return None

    def generate(self, word, hand_position="", movement="", meaning="", image_path=None):
        """Load the real sign image, with a safe lightweight fallback.

        No fake hand/rectangle is drawn anymore. If an asset exists, it is the
        image shown by Text -> Sign. Missing assets get a clear informational
        card instead of a misleading illustration.
        """
        asset_path = self.find_asset(word, image_path)
        if asset_path:
            image = self._load_asset(asset_path)
            if image is not None:
                return self._fit_image(image)

        return self._missing_asset_card(word, meaning)

    def _fit_image(self, image):
        image = image.copy()
        image.thumbnail((self.width - 16, self.height - 16), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (self.width, self.height), (15, 15, 26))
        x = (self.width - image.width) // 2
        y = (self.height - image.height) // 2
        canvas.paste(image, (x, y))
        return canvas

    def _missing_asset_card(self, word, meaning=""):
        bg = (15, 15, 26)
        accent = (233, 69, 96)
        white = (255, 255, 255)
        gray = (160, 160, 160)

        image = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, self.width, 6], fill=accent)
        draw.text((20, 24), str(word or "UNKNOWN"), font=self.title_font, fill=accent)
        draw.text((20, 78), "No sign reference asset found.", font=self.body_font, fill=white)
        draw.text((20, 108), "Add the matching PNG to:", font=self.small_font, fill=gray)
        draw.text((20, 130), "assets/signs/", font=self.body_font, fill=white)

        if meaning and meaning != "N/A":
            draw.text((20, 180), "MEANING", font=self.small_font, fill=gray)
            y = 202
            for line in self._wrap(str(meaning), 45)[:3]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 22

        draw.rectangle([0, self.height - 6, self.width, self.height], fill=accent)
        return image

    def _wrap(self, text, max_chars):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]
