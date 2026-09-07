"""
Text-to-Speech engine with cross-platform support.
On Arch Linux, requires: sudo pacman -S espeak-ng
"""
import platform
import subprocess
import os
import shutil

class TTSEngine:
    def __init__(self):
        self.system = platform.system()
        self.backend = None
        self._find_backend()

    def _find_backend(self):
        """Find the best available TTS backend."""
        # Check for espeak-ng first (modern, better quality)
        if shutil.which("espeak-ng"):
            self.backend = "espeak-ng"
            return
        # Check for legacy espeak
        if shutil.which("espeak"):
            self.backend = "espeak"
            return
        # Try pyttsx3 as last resort
        try:
            import pyttsx3
            engine = pyttsx3.init()
            # Test if it actually works
            engine.say("")
            engine.runAndWait()
            self.backend = "pyttsx3"
            self._pyttsx3_engine = engine
        except Exception:
            self.backend = None

    def speak(self, text):
        """Speak the given text. Returns (success, message)."""
        if not text or not text.strip():
            return False, "No text to speak"

        if self.backend in ("espeak-ng", "espeak"):
            try:
                cmd = [self.backend, text]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0:
                    return True, f"Spoke: {text[:40]}"
                else:
                    return False, f"{self.backend} error: {result.stderr.decode()[:100]}"
            except Exception as e:
                return False, f"TTS error: {str(e)}"

        elif self.backend == "pyttsx3":
            try:
                self._pyttsx3_engine.say(text)
                self._pyttsx3_engine.runAndWait()
                return True, f"Spoke: {text[:40]}"
            except Exception as e:
                return False, f"pyttsx3 error: {str(e)}"

        return False, "No TTS backend available. Install espeak-ng: sudo pacman -S espeak-ng"

    def get_status(self):
        """Get TTS availability status."""
        if self.backend:
            return f"TTS ready ({self.backend})"
        return "TTS not available. Install: sudo pacman -S espeak-ng"
