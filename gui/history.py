"""
Translation History Screen.
View and manage past translations.
"""
import tkinter as tk
from tkinter import ttk, messagebox, font

class HistoryFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")

        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        header = tk.Frame(self, bg="#16213e", height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        back_btn = tk.Button(header, text="← Back", font=("Helvetica", 12, "bold"),
                            bg="#16213e", fg="#e94560", relief=tk.FLAT,
                            command=lambda: self.controller.show_frame("Home"))
        back_btn.pack(side=tk.LEFT, padx=20, pady=10)

        title = tk.Label(header, text="Translation History",
                        font=("Helvetica", 18, "bold"), bg="#16213e", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Controls
        controls = tk.Frame(self, bg="#1a1a2e")
        controls.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(controls, text="🗑 Clear All History", font=("Helvetica", 11, "bold"),
                 bg="#e94560", fg="white", command=self._clear_all).pack(side=tk.LEFT, padx=5)

        tk.Button(controls, text="🔄 Refresh", font=("Helvetica", 11),
                 bg="#0f3460", fg="white", command=self._load_history).pack(side=tk.LEFT, padx=5)

        # Tree view
        tree_frame = tk.Frame(self, bg="#1a1a2e")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar_y = tk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Time", "Type", "Input", "Translation", "Confidence", "Lang"),
                                show="headings", yscrollcommand=scrollbar_y.set,
                                xscrollcommand=scrollbar_x.set)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Time", text="Timestamp")
        self.tree.heading("Type", text="Source")
        self.tree.heading("Input", text="Input")
        self.tree.heading("Translation", text="Translation")
        self.tree.heading("Confidence", text="Confidence")
        self.tree.heading("Lang", text="Language")

        self.tree.column("ID", width=50)
        self.tree.column("Time", width=150)
        self.tree.column("Type", width=80)
        self.tree.column("Input", width=200)
        self.tree.column("Translation", width=250)
        self.tree.column("Confidence", width=100)
        self.tree.column("Lang", width=80)

        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self._delete_selected)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Detail view
        detail_frame = tk.Frame(self, bg="#16213e", height=100)
        detail_frame.pack(fill=tk.X, padx=20, pady=10)
        detail_frame.pack_propagate(False)

        self.detail_label = tk.Label(detail_frame, text="Right-click an entry to delete it. History is stored locally.",
                                    font=("Helvetica", 11), bg="#16213e", fg="#888888",
                                    wraplength=700, justify=tk.LEFT)
        self.detail_label.pack(pady=20)

    def _load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        history = self.controller.db.get_history(limit=100)
        for entry in history:
            self.tree.insert("", tk.END, values=(
                entry[0], entry[1], entry[2], entry[3][:50] if entry[3] else "N/A",
                entry[4], f"{entry[5]*100:.1f}%" if entry[5] else "N/A", entry[6]
            ))

    def _clear_all(self):
        if messagebox.askyesno("Confirm", "Delete all translation history?"):
            self.controller.db.clear_history()
            self._load_history()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        item_id = item['values'][0]

        if messagebox.askyesno("Confirm", "Delete this entry?"):
            self.controller.db.delete_history_item(item_id)
            self._load_history()

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_hide(self):
        pass
