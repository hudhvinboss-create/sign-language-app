#!/usr/bin/env python3
"""
Auto-fix script for sign_language_app
Run this from inside the sign_language_app folder.
"""
import os
import sys
import shutil
import subprocess

print("=" * 50)
print("Sign Language App - Auto Fix & Run")
print("=" * 50)

# 1. Check espeak-ng
print("\n[1/4] Checking TTS...")
if not shutil.which("espeak-ng"):
    print("   espeak-ng NOT found.")
    print("   Run this in another terminal:")
    print("   sudo pacman -S espeak-ng")
    print("   Then re-run this script.\n")
else:
    print(f"   espeak-ng found: {shutil.which('espeak-ng')}")

# 2. Fix image_generator.py
print("\n[2/4] Fixing image_generator.py...")
img_gen_content = """from PIL import Image, ImageDraw, ImageFont
import os

class SignImageGenerator:
    def __init__(self, width=400, height=300):
        self.width = width
        self.height = height
        self.title_font = self._find_font(28)
        self.body_font = self._find_font(12)
        self.small_font = self._find_font(10)

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
        draw.rectangle([0, 0, self.width, 6], fill=accent)
        draw.text((20, 25), word, font=self.title_font, fill=accent)

        # Hand icon
        x, y = 300, 50
        draw.rectangle([x, y+30, x+40, y+70], outline=accent, width=2)
        for i in range(5):
            fx = x + 5 + i * 7
            draw.line([(fx, y+30), (fx, y)], fill=accent, width=2)

        y = 80
        if meaning and meaning != "N/A":
            draw.text((20, y), "MEANING", font=self.small_font, fill=gray)
            y += 16
            for line in self._wrap(meaning, 50)[:3]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 16
            y += 8

        if hand_position and hand_position != "N/A":
            draw.text((20, y), "HAND POSITION", font=self.small_font, fill=gray)
            y += 16
            for line in self._wrap(hand_position, 55)[:2]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 16
            y += 8

        if movement and movement != "N/A":
            draw.text((20, y), "MOVEMENT", font=self.small_font, fill=gray)
            y += 16
            for line in self._wrap(movement, 55)[:2]:
                draw.text((20, y), line, font=self.body_font, fill=white)
                y += 16

        draw.rectangle([0, self.height-4, self.width, self.height], fill=accent)
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
"""

with open("utils/image_generator.py", "w") as f:
    f.write(img_gen_content)
print("   image_generator.py FIXED")

# 3. Fix tts_engine.py
print("\n[3/4] Fixing tts_engine.py...")
tts_content = """import platform
import subprocess
import shutil

class TTSEngine:
    def __init__(self):
        self.backend = None
        if shutil.which("espeak-ng"):
            self.backend = "espeak-ng"
        elif shutil.which("espeak"):
            self.backend = "espeak"
        else:
            try:
                import pyttsx3
                e = pyttsx3.init()
                e.say("")
                e.runAndWait()
                self.backend = "pyttsx3"
                self._engine = e
            except:
                pass

    def speak(self, text):
        if not text or not text.strip():
            return False, "No text"
        if self.backend in ("espeak-ng", "espeak"):
            r = subprocess.run([self.backend, text], capture_output=True, timeout=30)
            return (r.returncode == 0, f"Spoke: {text[:40]}")
        elif self.backend == "pyttsx3":
            self._engine.say(text)
            self._engine.runAndWait()
            return True, f"Spoke: {text[:40]}"
        return False, "No TTS. Install: sudo pacman -S espeak-ng"

    def get_status(self):
        return f"TTS ready ({self.backend})" if self.backend else "TTS not available. Install: sudo pacman -S espeak-ng"
"""

with open("utils/tts_engine.py", "w") as f:
    f.write(tts_content)
print("   tts_engine.py FIXED")

# 4. Verify imports work
print("\n[4/4] Testing imports...")
try:
    from utils.image_generator import SignImageGenerator
    gen = SignImageGenerator()
    img = gen.generate("HELLO", "Open hand", "Wave", "Greeting")
    print(f"   Image generation: OK ({img.size})")
except Exception as e:
    print(f"   Image generation FAILED: {e}")
    sys.exit(1)

try:
    from utils.tts_engine import TTSEngine
    tts = TTSEngine()
    print(f"   TTS backend: {tts.get_status()}")
except Exception as e:
    print(f"   TTS FAILED: {e}")

print("\n" + "=" * 50)
print("All fixes applied successfully!")
print("Launching app now...")
print("=" * 50 + "\n")

# Launch the app
os.system("python main.py")
