"""
Sign Language Dictionary Screen.
Searchable dictionary with categories.
"""
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
from utils.image_generator import SignImageGenerator

class DictionaryFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")
        self.image_gen = SignImageGenerator()
        self.current_tk_image = None

        self._setup_ui()
        self._load_categories()
        self._load_signs()

    def _setup_ui(self):
        header = tk.Frame(self, bg="#16213e", height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        back_btn = tk.Button(header, text="← Back", font=("Helvetica", 12, "bold"),
                            bg="#16213e", fg="#e94560", relief=tk.FLAT,
                            command=lambda: self.controller.show_frame("Home"))
        back_btn.pack(side=tk.LEFT, padx=20, pady=10)

        title = tk.Label(header, text="Sign Language Dictionary",
                        font=("Helvetica", 18, "bold"), bg="#16213e", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        content = tk.Frame(self, bg="#1a1a2e")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Search panel
        search_frame = tk.Frame(content, bg="#16213e", height=60)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        search_frame.pack_propagate(False)

        tk.Label(search_frame, text="Search:", font=("Helvetica", 12),
                bg="#16213e", fg="white").pack(side=tk.LEFT, padx=20, pady=15)

        self.search_entry = tk.Entry(search_frame, font=("Helvetica", 12),
                                    bg="#0f0f1a", fg="white", width=25)
        self.search_entry.pack(side=tk.LEFT, padx=10, pady=15)
        self.search_entry.bind("<Return>", lambda e: self._search())

        tk.Button(search_frame, text="🔍 Search", font=("Helvetica", 11, "bold"),
                 bg="#e94560", fg="white", command=self._search).pack(side=tk.LEFT, padx=5, pady=15)

        tk.Button(search_frame, text="🔄 Reset", font=("Helvetica", 11),
                 bg="#533483", fg="white", command=self._load_signs).pack(side=tk.LEFT, padx=5, pady=15)

        # Category filter
        tk.Label(search_frame, text="Category:", font=("Helvetica", 12),
                bg="#16213e", fg="white").pack(side=tk.LEFT, padx=(30, 10), pady=15)

        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var,
                                          state="readonly", width=15, font=("Helvetica", 11))
        self.category_combo.pack(side=tk.LEFT, padx=5, pady=15)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self._load_signs())

        # Main display
        main_frame = tk.Frame(content, bg="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Signs list
        list_frame = tk.Frame(main_frame, bg="#1a1a2e", width=250)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        list_frame.pack_propagate(False)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.signs_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                       font=("Helvetica", 12, "bold"),
                                       bg="#0f0f1a", fg="white",
                                       selectbackground="#e94560",
                                       height=20)
        self.signs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.signs_listbox.yview)

        self.signs_listbox.bind("<<ListboxSelect>>", self._on_select)

        # Right panel - Details + Image
        right_panel = tk.Frame(main_frame, bg="#16213e")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # Sign image
        self.sign_image_label = tk.Label(right_panel, bg="#0f0f1a", bd=2, relief=tk.SUNKEN,
                                        text="Select a sign to view", fg="#888888",
                                        font=("Helvetica", 12))
        self.sign_image_label.pack(pady=(20, 10), padx=20)

        self.detail_word = tk.Label(right_panel, text="",
                                   font=("Helvetica", 24, "bold"),
                                   bg="#16213e", fg="#e94560")
        self.detail_word.pack(pady=(10, 5))

        self.detail_category = tk.Label(right_panel, text="",
                                       font=("Helvetica", 12),
                                       bg="#16213e", fg="#888888")
        self.detail_category.pack(pady=5)

        info_frame = tk.Frame(right_panel, bg="#16213e")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        fields = [
            ("Meaning", "detail_meaning"),
            ("Hand Position", "detail_hand"),
            ("Movement", "detail_movement"),
            ("Example Sentence", "detail_example"),
            ("Related Signs", "detail_related")
        ]

        self.detail_labels = {}
        for label_text, attr_name in fields:
            frame = tk.Frame(info_frame, bg="#16213e")
            frame.pack(fill=tk.X, pady=6)

            tk.Label(frame, text=f"{label_text}:", font=("Helvetica", 11, "bold"),
                    bg="#16213e", fg="#4ecca3").pack(anchor=tk.W)

            label = tk.Label(frame, text="---", font=("Helvetica", 10),
                            bg="#16213e", fg="white", wraplength=450, justify=tk.LEFT)
            label.pack(anchor=tk.W, pady=(2, 0))
            self.detail_labels[attr_name] = label

    def _load_categories(self):
        categories = self.controller.db.get_categories(self.controller.language)
        categories.insert(0, "All")
        self.category_combo['values'] = categories

    def _load_signs(self):
        category = self.category_var.get()
        signs = self.controller.db.get_all_signs(self.controller.language, category)

        self.signs_listbox.delete(0, tk.END)
        self.all_signs = signs

        for sign in signs:
            self.signs_listbox.insert(tk.END, sign[1])

    def _search(self):
        query = self.search_entry.get().strip()
        if not query:
            self._load_signs()
            return

        category = self.category_var.get()
        results = self.controller.db.search_signs(query, self.controller.language, 
                                                 category if category != "All" else None)

        self.signs_listbox.delete(0, tk.END)
        self.all_signs = results

        for sign in results:
            self.signs_listbox.insert(tk.END, sign[1])

    def _on_select(self, event):
        selection = self.signs_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < len(self.all_signs):
            sign = self.all_signs[idx]
            self._display_sign_details(sign)

    def _display_sign_details(self, sign):
        word = sign[1]
        meaning = sign[4] or ""
        hand_pos = sign[5] or ""
        movement = sign[6] or ""

        self.detail_word.config(text=word)
        self.detail_category.config(text=f"Category: {sign[3]} | Language: {sign[2]}")

        # Generate and display sign image
        try:
            pil_img = self.image_gen.generate(word, hand_pos, movement, meaning)
            pil_img = pil_img.resize((380, 280), Image.Resampling.LANCZOS)
            self.current_tk_image = ImageTk.PhotoImage(pil_img)
            self.sign_image_label.config(image=self.current_tk_image, text="")
        except Exception as e:
            self.sign_image_label.config(image="", text=f"[{word}]")
            print(f"Image generation error: {e}")

        self.detail_labels["detail_meaning"].config(text=sign[4] or "N/A")
        self.detail_labels["detail_hand"].config(text=sign[5] or "N/A")
        self.detail_labels["detail_movement"].config(text=sign[6] or "N/A")
        self.detail_labels["detail_example"].config(text=sign[7] or "N/A")
        self.detail_labels["detail_related"].config(text=sign[8] or "N/A")

    def on_hide(self):
        pass
