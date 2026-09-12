"""
Sign Language Reference Image Loader.

Text -> Sign uses SVG reference artwork and never falls back to the old
legacy PNG placeholder cards.
"""

import io
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

try:
    import resvg_py
except ImportError:
    resvg_py = None


class SignImageGenerator:
    def __init__(self, width=400, height=300):
        self.width = width
        self.height = height
        self.title_font = self._find_font(28, bold=True)
        self.body_font = self._find_font(15)
        self.small_font = self._find_font(12)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.asset_root = os.path.join(self.project_root, "assets")
        self.sign_asset_dir = os.path.join(self.asset_root, "signs")
        self.phrase_asset_dir = os.path.join(self.asset_root, "phrases")
        self.alphabet_asset_dir = os.path.join(self.asset_root, "alphabet")
        self.number_asset_dir = os.path.join(self.asset_root, "numbers")

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
        return value

    def _candidate_paths(self, word, image_path=None):
        candidates = []
        raw = self._normalise_name(word)
        underscore = raw.replace("-", "_").replace(" ", "_")
        hyphen = raw.replace(" ", "-").replace("_", "-")

        if raw:
            names = []
            for name in (raw, underscore, hyphen):
                if name and name not in names:
                    names.append(name)

            if len(underscore) == 1 and underscore.isalpha():
                for name in names:
                    candidates.append(os.path.join(self.alphabet_asset_dir, f"{name}.svg"))
            elif underscore.isdigit():
                for name in names:
                    candidates.append(os.path.join(self.number_asset_dir, f"{name}.svg"))
            elif "_" in underscore or "-" in raw or " " in raw:
                for name in names:
                    candidates.append(os.path.join(self.phrase_asset_dir, f"{name}.svg"))
                    candidates.append(os.path.join(self.sign_asset_dir, f"{name}.svg"))
            else:
                for name in names:
                    candidates.append(os.path.join(self.sign_asset_dir, f"{name}.svg"))
                    candidates.append(os.path.join(self.phrase_asset_dir, f"{name}.svg"))

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
            if path.lower().endswith(".svg"):
                if resvg_py is None:
                    raise RuntimeError("SVG renderer unavailable. Run: pip install resvg_py")
                png_bytes = resvg_py.svg_to_bytes(
                    svg_path=path,
                    width=self.width,
                    height=self.height,
                )
                with Image.open(io.BytesIO(png_bytes)) as source:
                    return source.convert("RGB").copy()

            # Deliberately do not load legacy PNG assets because they contain
            # the old placeholder/brick artwork.
            return None
        except (OSError, ValueError, RuntimeError, TypeError) as exc:
            print(f"[Text->Sign] Could not load asset '{path}': {exc}")
            return None

    def find_asset(self, word, image_path=None):
        for path in self._candidate_paths(word, image_path):
            if os.path.isfile(path):
                print(f"[Text->Sign] Using sign asset: {path}")
                return path
        return None

    def generate(self, word, hand_position="", movement="", meaning="", image_path=None):
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
        image = Image.new("RGB", (self.width, self.height), (15, 15, 26))
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, self.width, 6], fill=(233, 69, 96))
        draw.text((20, 24), str(word or "UNKNOWN"), font=self.title_font, fill=(233, 69, 96))
        draw.text((20, 78), "No SVG sign reference found.", font=self.body_font, fill=(255, 255, 255))
        draw.text((20, 108), "The legacy brick image is disabled.", font=self.small_font, fill=(160, 160, 160))
        draw.rectangle([0, self.height - 6, self.width, self.height], fill=(233, 69, 96))
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
