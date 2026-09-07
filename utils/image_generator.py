from PIL import Image, ImageDraw, ImageFont
import os

class SignImageGenerator:
    def __init__(self, width=400, height=300):
        self.width = width
        self.height = height
        self.title_font = self._find_font(36)
        self.body_font = self._find_font(16)
        self.small_font = self._find_font(13)

    def _find_font(self, size):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except:
                    pass
        return ImageFont.load_default()

    def generate(self, word, hand_position="", movement="", meaning=""):
        bg = (15, 15, 26)
        accent = (233, 69, 96)
        white = (255, 255, 255)
        gray = (160, 160, 160)

        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, self.width, 8], fill=accent)
        draw.text((20, 20), word, font=self.title_font, fill=accent)

        x, y = 310, 40
        draw.rectangle([x, y+35, x+45, y+75], outline=accent, width=3)
        for i in range(5):
            fx = x + 5 + i * 8
            draw.line([(fx, y+35), (fx, y+5)], fill=accent, width=3)

        y = 75
        if meaning and meaning != "N/A":
            draw.text((20, y), "MEANING", font=self.small_font, fill=gray)
            y += 20
            for line in self._wrap(meaning, 48)[:3]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 22
            y += 10

        if hand_position and hand_position != "N/A":
            draw.text((20, y), "HAND POSITION", font=self.small_font, fill=gray)
            y += 20
            for line in self._wrap(hand_position, 52)[:2]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 22
            y += 10

        if movement and movement != "N/A":
            draw.text((20, y), "MOVEMENT", font=self.small_font, fill=gray)
            y += 20
            for line in self._wrap(movement, 52)[:2]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 22

        draw.rectangle([0, self.height-6, self.width, self.height], fill=accent)
        return img

    def _wrap(self, text, max_chars):
        if not text:
            return [""]
        words = text.split()
        lines, current = [], ""
        for w in words:
            if len(current) + len(w) + 1 <= max_chars:
                current += (" " if current else "") + w
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines if lines else [text]
