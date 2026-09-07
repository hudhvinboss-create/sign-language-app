"""
Learning Resources Screen.
Shows free PDF books and external references from infobooks.org and other sources.
"""
import tkinter as tk
from tkinter import ttk, font
import webbrowser

class ResourcesFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")

        self._setup_ui()
        self._load_resources()

    def _setup_ui(self):
        header = tk.Frame(self, bg="#16213e", height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        back_btn = tk.Button(header, text="← Back", font=("Helvetica", 12, "bold"),
                            bg="#16213e", fg="#e94560", relief=tk.FLAT,
                            command=lambda: self.controller.show_frame("Home"))
        back_btn.pack(side=tk.LEFT, padx=20, pady=10)

        title = tk.Label(header, text="Free Learning Resources",
                        font=("Helvetica", 18, "bold"), bg="#16213e", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Filter controls
        filter_frame = tk.Frame(self, bg="#16213e", height=50)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        filter_frame.pack_propagate(False)

        tk.Label(filter_frame, text="Language:", font=("Helvetica", 11),
                bg="#16213e", fg="white").pack(side=tk.LEFT, padx=(20, 5), pady=10)

        self.lang_var = tk.StringVar(value="All")
        lang_combo = ttk.Combobox(filter_frame, textvariable=self.lang_var,
                                  values=["All", "ASL", "BSL", "SASL", "Makaton", "Multiple"],
                                  state="readonly", width=12, font=("Helvetica", 10))
        lang_combo.pack(side=tk.LEFT, padx=5, pady=10)
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._load_resources())

        tk.Label(filter_frame, text="Category:", font=("Helvetica", 11),
                bg="#16213e", fg="white").pack(side=tk.LEFT, padx=(20, 5), pady=10)

        self.cat_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(filter_frame, textvariable=self.cat_var,
                                 values=["All", "Beginner", "Dictionary", "Education", 
                                        "Medical", "Standards", "Special Populations", "Reference"],
                                 state="readonly", width=15, font=("Helvetica", 10))
        cat_combo.pack(side=tk.LEFT, padx=5, pady=10)
        cat_combo.bind("<<ComboboxSelected>>", lambda e: self._load_resources())

        # Resources list
        list_frame = tk.Frame(self, bg="#1a1a2e")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.resources_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=("Helvetica", 12, "bold"),
                                        bg="#0f0f1a", fg="white",
                                        selectbackground="#e94560",
                                        height=15)
        self.resources_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.resources_list.yview)

        self.resources_list.bind("<<ListboxSelect>>", self._on_select)

        # Detail panel
        detail_frame = tk.Frame(self, bg="#16213e", height=200)
        detail_frame.pack(fill=tk.X, padx=20, pady=10)
        detail_frame.pack_propagate(False)

        self.detail_title = tk.Label(detail_frame, text="Select a resource",
                                    font=("Helvetica", 16, "bold"),
                                    bg="#16213e", fg="#e94560")
        self.detail_title.pack(pady=(15, 5))

        self.detail_author = tk.Label(detail_frame, text="",
                                     font=("Helvetica", 11),
                                     bg="#16213e", fg="#888888")
        self.detail_author.pack(pady=2)

        self.detail_desc = tk.Label(detail_frame, text="",
                                   font=("Helvetica", 10),
                                   bg="#16213e", fg="white",
                                   wraplength=900, justify=tk.LEFT)
        self.detail_desc.pack(pady=5, padx=20)

        self.detail_meta = tk.Label(detail_frame, text="",
                                   font=("Helvetica", 10),
                                   bg="#16213e", fg="#4ecca3")
        self.detail_meta.pack(pady=5)

        btn_frame = tk.Frame(detail_frame, bg="#16213e")
        btn_frame.pack(pady=10)

        self.open_btn = tk.Button(btn_frame, text="🔗 Open in Browser", 
                                 font=("Helvetica", 11, "bold"),
                                 bg="#e94560", fg="white",
                                 command=self._open_url, state=tk.DISABLED)
        self.open_btn.pack(side=tk.LEFT, padx=5)

    def _load_resources(self):
        self.resources_list.delete(0, tk.END)
        self.all_resources = self.controller.db.get_resources(
            self.lang_var.get() if self.lang_var.get() != "All" else None,
            self.cat_var.get() if self.cat_var.get() != "All" else None
        )

        for res in self.all_resources:
            display = f"{res[1]} ({res[5]} pages) [{res[6]}]"
            self.resources_list.insert(tk.END, display)

    def _on_select(self, event):
        selection = self.resources_list.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < len(self.all_resources):
            res = self.all_resources[idx]
            self.detail_title.config(text=res[1])
            self.detail_author.config(text=f"By: {res[2] or 'Unknown'}")
            self.detail_desc.config(text=res[3] or "No description available.")
            self.detail_meta.config(text=f"Language: {res[5]} | Category: {res[7]} | Format: {res[8]} | {res[6]} pages")
            self.current_url = res[4]
            self.open_btn.config(state=tk.NORMAL)

    def _open_url(self):
        if hasattr(self, 'current_url') and self.current_url:
            webbrowser.open(self.current_url)

    def on_hide(self):
        pass
