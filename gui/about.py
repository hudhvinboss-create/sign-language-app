import tkinter as tk
from tkinter import ttk

class AboutFrame(tk.Frame):
    def __init__(self,parent,controller,*args,**kwargs):
        super().__init__(parent,*args,**kwargs); self.controller=controller; self.configure(bg="#1a1a2e")
        tk.Button(self,text="← Back",command=lambda: controller.show_frame("Home"),bg="#16213e",fg="#e94560",relief=tk.FLAT).pack(anchor="w",padx=20,pady=15)
        tk.Label(self,text="ℹ️ About & Learning",font=("Helvetica",26,"bold"),bg="#1a1a2e",fg="#e94560").pack(pady=10)
        text=tk.Text(self,bg="#0f0f1a",fg="white",font=("Helvetica",12),wrap=tk.WORD,relief=tk.FLAT)
        text.pack(fill=tk.BOTH,expand=True,padx=35,pady=20)
        text.insert("end", "SIGN LANGUAGE TRANSLATOR\n\nThis prototype combines a local dictionary, computer-vision translation experiments, Text → Sign reference cards, history, and learning resources.\n\nLEARNING NOTE\nSign languages are natural languages. English word order does not always map directly to ASL, ISL, or BSL. Facial expression, movement, and context can carry meaning.\n\nASSET PACK\n• 114+ dictionary reference cards\n• A-Z fingerspelling cards\n• Numbers 0-9\n• Common phrase cards\n• Detailed metadata, tags, examples, movement and hand-position descriptions\n\nThe visual cards are educational references, not machine-learning training samples. Verify signs with authoritative learning resources before relying on them for important communication.")
        text.config(state=tk.DISABLED)
