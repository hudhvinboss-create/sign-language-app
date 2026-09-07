import tkinter as tk
import sqlite3
import os

class StatsFrame(tk.Frame):
    def __init__(self,parent,controller,*args,**kwargs):
        super().__init__(parent,*args,**kwargs); self.controller=controller; self.configure(bg="#1a1a2e")
        tk.Button(self,text="← Back",command=lambda: controller.show_frame("Home"),bg="#16213e",fg="#e94560",relief=tk.FLAT).pack(anchor="w",padx=20,pady=15)
        tk.Label(self,text="📊 Vocabulary Statistics",font=("Helvetica",26,"bold"),bg="#1a1a2e",fg="#e94560").pack(pady=10)
        body=tk.Frame(self,bg="#1a1a2e"); body.pack(fill=tk.BOTH,expand=True,padx=40,pady=20)
        db_path=os.path.join(os.path.dirname(os.path.dirname(__file__)),"database","signs.db")
        con=sqlite3.connect(db_path); cur=con.cursor()
        total=cur.execute("SELECT COUNT(*) FROM signs").fetchone()[0]
        cats=cur.execute("SELECT category, COUNT(*) FROM signs GROUP BY category ORDER BY COUNT(*) DESC").fetchall()
        langs=cur.execute("SELECT language, COUNT(*) FROM signs GROUP BY language").fetchall(); con.close()
        cards=[("DICTIONARY SIGNS",str(total)),("ALPHABET","26"),("NUMBERS","10"),("COMMON PHRASES","12")]
        for i,(a,b) in enumerate(cards):
            f=tk.Frame(body,bg="#16213e",bd=2,relief=tk.RIDGE); f.grid(row=0,column=i,padx=8,sticky="nsew"); body.grid_columnconfigure(i,weight=1)
            tk.Label(f,text=b,font=("Helvetica",28,"bold"),bg="#16213e",fg="#e94560").pack(pady=(18,3)); tk.Label(f,text=a,font=("Helvetica",10,"bold"),bg="#16213e",fg="white").pack(pady=(0,18))
        report=tk.Text(body,bg="#0f0f1a",fg="white",font=("Helvetica",12),wrap=tk.WORD,relief=tk.FLAT); report.grid(row=1,column=0,columnspan=4,sticky="nsew",pady=25); body.grid_rowconfigure(1,weight=1)
        report.insert("end","CATEGORIES\n\n")
        for cat,n in cats: report.insert("end",f"• {cat}: {n} signs\n")
        report.insert("end","\nLANGUAGES IN DATABASE\n\n")
        for lang,n in langs: report.insert("end",f"• {lang}: {n} signs\n")
        report.insert("end","\nASSET PACK\n\n• 114 dictionary cards\n• 26 alphabet cards\n• 10 number cards\n• 12 phrase cards\n• Machine-readable asset_index.json and MANIFEST.json")
        report.config(state=tk.DISABLED)
