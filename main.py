"""
Sign Language Translator Application
Main entry point and controller.
"""
import tkinter as tk
from tkinter import ttk, font
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import SignDatabase
from gui.home import HomeFrame
from gui.live_translation import LiveTranslationFrame
from gui.video_translation import VideoTranslationFrame
from gui.text_to_sign import TextToSignFrame
from gui.dictionary import DictionaryFrame
from gui.history import HistoryFrame
from gui.resources import ResourcesFrame

class SignLanguageApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("AI Sign Language Translator")
        self.geometry("1200x800")
        self.configure(bg="#1a1a2e")
        self.minsize(1000, 700)

        self.db = SignDatabase()
        self.language = self.db.get_setting("language", "ASL")

        self._setup_styles()

        container = tk.Frame(self, bg="#1a1a2e")
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        frame_classes = {
            "Home": HomeFrame,
            "LiveTranslation": LiveTranslationFrame,
            "VideoTranslation": VideoTranslationFrame,
            "TextToSign": TextToSignFrame,
            "Dictionary": DictionaryFrame,
            "History": HistoryFrame,
            "Resources": ResourcesFrame,
        }

        for name, F in frame_classes.items():
            frame = F(container, self, bg="#1a1a2e")
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Home")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground="#0f0f1a", background="#16213e",
                       foreground="white", arrowcolor="white")
        style.configure("TProgressbar", background="#e94560", troughcolor="#0f0f1a")
        style.configure("Treeview", background="#0f0f1a", foreground="white",
                       fieldbackground="#0f0f1a")
        style.configure("Treeview.Heading", background="#16213e", foreground="white")

    def show_frame(self, page_name):
        for name, frame in self.frames.items():
            if frame.winfo_viewable() and hasattr(frame, 'on_hide'):
                frame.on_hide()

        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def set_language(self, lang):
        self.language = lang
        self.db.set_setting("language", lang)
        print(f"Language changed to: {lang}")

if __name__ == "__main__":
    app = SignLanguageApp()
    app.mainloop()
