"""
Text-to-Speech engine with cross-platform support.
On Arch Linux, requires: sudo pacman -S espeak-ng
"""
import platform
import subprocess
import os
import shutil
import threading

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
        # Try pyttsx3 as last resort. NOTE: we only use this to confirm a
        # backend is available -- we do NOT keep this engine instance around.
        # On Windows (SAPI5), calling say()+runAndWait() a second time on an
        # already-used engine instance is a well-known hang/crash bug, so a
        # fresh engine is created per speak() call instead (see speak()).
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say("")
            engine.runAndWait()
            engine.stop()
            self.backend = "pyttsx3"
        except Exception:
            self.backend = None

    def speak(self, text):
        """
        Speak the given text synchronously. Returns (success, message).
        NOTE: this blocks for the duration of speech -- prefer speak_async()
        from GUI code so the Tkinter main thread doesn't freeze.
        """
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
                import pyttsx3
                # Fresh engine per call -- reusing one instance across calls
                # is what causes the Windows SAPI5 hang on the 2nd+ call.
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                return True, f"Spoke: {text[:40]}"
            except Exception as e:
                return False, f"pyttsx3 error: {str(e)}"

        return False, "No TTS backend available. Install espeak-ng: sudo pacman -S espeak-ng"

    def speak_async(self, text, callback=None):
        """
        Speak text on a background thread so the caller (e.g. the Tkinter
        main thread) never blocks. If provided, callback(success, message)
        is invoked from the background thread when done -- GUI code should
        marshal it back with e.g. self.after(0, callback, success, message),
        since Tkinter widgets must only be touched from the main thread.
        """
        def _run():
            success, message = self.speak(text)
            if callback:
                callback(success, message)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    def get_status(self):
        """Get TTS availability status."""
        if self.backend:
            return f"TTS ready ({self.backend})"
        return "TTS not available. Install: sudo pacman -S espeak-ng"
