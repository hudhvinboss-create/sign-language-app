"""
Home screen / Main navigation panel.
"""
import tkinter as tk
from tkinter import ttk, font

class HomeFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")

        title_font = font.Font(family="Helvetica", size=32, weight="bold")
        subtitle_font = font.Font(family="Helvetica", size=14)

        title = tk.Label(self, text="Sign Language Translator", 
                        font=title_font, bg="#1a1a2e", fg="#e94560")
        title.pack(pady=(40, 10))

        subtitle = tk.Label(self, text="AI-Powered Translation for ASL, ISL, and BSL",
                           font=subtitle_font, bg="#1a1a2e", fg="#a0a0a0")
        subtitle.pack(pady=(0, 40))

        lang_frame = tk.Frame(self, bg="#1a1a2e")
        lang_frame.pack(pady=20)

        tk.Label(lang_frame, text="Select Sign Language:", 
                font=subtitle_font, bg="#1a1a2e", fg="#ffffff").pack(side=tk.LEFT, padx=10)

        self.lang_var = tk.StringVar(value="ASL")
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, 
                                  values=["ASL", "ISL", "BSL"], 
                                  state="readonly", width=15, font=("Helvetica", 12))
        lang_combo.pack(side=tk.LEFT, padx=10)
        lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        btn_frame = tk.Frame(self, bg="#1a1a2e")
        btn_frame.pack(pady=30)

        buttons = [
            ("🔴 Live Translation", "#e94560", self._go_live),
            ("📁 Upload Video", "#0f3460", self._go_video),
            ("⌨️ Text → Sign", "#533483", self._go_text),
            ("📖 Sign Dictionary", "#16213e", self._go_dict),
            ("📚 Free Resources", "#1a4d2e", self._go_resources),
            ("📜 History", "#1a1a2e", self._go_history),
            ("📊 Vocabulary Stats", "#24445c", self._go_stats),
            ("ℹ️ About & Learning", "#3d315c", self._go_about),
        ]

        for text, color, command in buttons:
            btn = tk.Button(btn_frame, text=text, font=("Helvetica", 16, "bold"),
                           bg=color, fg="white", width=20, height=2,
                           relief=tk.FLAT, cursor="hand2",
                           command=command)
            btn.pack(pady=10)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#2a2a4e"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))

    def _on_lang_change(self, event=None):
        self.controller.set_language(self.lang_var.get())

    def _go_live(self):
        self.controller.show_frame("LiveTranslation")

    def _go_video(self):
        self.controller.show_frame("VideoTranslation")

    def _go_text(self):
        self.controller.show_frame("TextToSign")

    def _go_dict(self):
        self.controller.show_frame("Dictionary")

    def _go_resources(self):
        self.controller.show_frame("Resources")

    def _go_history(self):
        self.controller.show_frame("History")

    def _go_stats(self):
        self.controller.show_frame("Stats")

    def _go_about(self):
        self.controller.show_frame("About")
