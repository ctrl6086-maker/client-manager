"""
ממשק גרפי (חלונות) לניהול לקוחות, חשבונות Gmail, וסנכרון/דוחות.
זהו נקודת הכניסה הראשית של התוכנה.
"""
import os
import sys
import shutil
import threading
import queue
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

import clients as clients_db
import accounts as accounts_db
import report as report_mod
import sync as sync_mod
import gmail_client
from paths import get_base_dir

APP_TITLE = "ניהול לקוחות ודוחות Gmail"


class AddClientDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("הוספת לקוח")
        self.result = None
        self.resizable(False, False)
        self.transient(parent)

        pad = {"padx": 8, "pady": 6}
        ttk.Label(self, text="שם:").grid(row=0, column=1, sticky="e", **pad)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=32).grid(row=0, column=0, **pad)

        ttk.Label(self, text="אימייל:").grid(row=1, column=1, sticky="e", **pad)
        self.email_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.email_var, width=32).grid(row=1, column=0, **pad)

        ttk.Label(self, text="הערות (לא חובה):").grid(row=2, column=1, sticky="e", **pad)
        self.notes_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.notes_var, width=32).grid(row=2, column=0, **pad)

        btns = ttk.Frame(self)
        btns.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="הוסף", command=self._on_ok).pack(side="right", padx=4)
        ttk.Button(btns, text="ביטול", command=self.destroy).pack(side="right", padx=4)

        self.grab_set()
        self.wait_visibility()
        self.focus()

    def _on_ok(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        if not name or not email:
            messagebox.showerror(APP_TITLE, "יש למלא שם ואימייל", parent=self)
            return
        self.result = (name, email, self.notes_var.get().strip())
        self.destroy()


class ClientManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("880x640")
        self.minsize(700, 500)
        self.msg_queue = queue.Queue()

        self._build_ui()
        self._poll_queue()

    # ---------------- overall layout ----------------
    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.clients_tab = ttk.Frame(notebook)
        self.accounts_tab = ttk.Frame(notebook)
        self.sync_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)

        notebook.add(self.settings_tab, text="הגדרות")
        notebook.add(self.clients_tab, text="לקוחות")
        notebook.add(self.accounts_tab, text="חשבונות Gmail")
        notebook.add(self.sync_tab, text="סנכרון ודוחות")

        self._build_settings_tab()
        self._build_clients_tab()
        self._build_accounts_tab()
        self._build_sync_tab()

        log_frame = ttk.LabelFrame(self, text="יומן פעילות")
        log_frame.pack(fill="both", padx=10, pady=10)
        self.log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

    def _log(self, msg):
        self.msg_queue.put(msg)

    def _poll_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert("end", msg + "\n")
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        self.after(200, self._poll_queue)

    # ---------------- settings tab ----------------
    def _build_settings_tab(self):
        frame = self.settings_tab

        ttk.Label(frame, text="חיבור ל-Google (חד פעמי בלבד)", font=("", 13, "bold")).pack(
            anchor="e", padx=15, pady=(20, 5)
        )
        ttk.Label(
            frame,
            text="כדי שהתוכנה תוכל לגשת ל-Gmail שלך, צריך פעם אחת קובץ הרשאות\n"
                 "אישי מ-Google (חינמי). ההוראות המלאות איך להשיג אותו נמצאות\n"
                 "בקובץ README.md שמגיע עם התוכנה. לאחר שהורדת אותו למחשב,\n"
                 "לחץ כאן לבחור אותו - אין צורך להעתיק קבצים ידנית:",
            justify="right", wraplength=560,
        ).pack(anchor="e", padx=15, pady=(0, 10))

        self.cred_status_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.cred_status_var, font=("", 11, "bold")).pack(
            anchor="e", padx=15, pady=5
        )

        ttk.Button(frame, text="📁  בחר קובץ הרשאות (credentials.json)...", command=self._import_credentials).pack(
            anchor="e", padx=15, pady=5
        )

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=15, pady=20)
        ttk.Label(
            frame,
            text="לאחר שחיברת את קובץ ההרשאות, עברו ללשונית 'חשבונות Gmail'\n"
                 "כדי לחבר את חשבונות ה-Gmail עצמם.",
            justify="right",
        ).pack(anchor="e", padx=15)

        self._refresh_credentials_status()

    def _credentials_path(self):
        return os.path.join(get_base_dir(), "credentials.json")

    def _refresh_credentials_status(self):
        if os.path.exists(self._credentials_path()):
            self.cred_status_var.set("✅ קובץ ההרשאות מחובר - אפשר להמשיך לחבר חשבונות")
        else:
            self.cred_status_var.set("❌ עדיין לא חובר קובץ הרשאות")

    def _import_credentials(self):
        path = filedialog.askopenfilename(
            title="בחר את קובץ ה-credentials.json שהורדת מ-Google",
            filetypes=[("קובצי JSON", "*.json"), ("כל הקבצים", "*.*")],
        )
        if not path:
            return
        try:
            shutil.copy(path, self._credentials_path())
            self._log("✅ קובץ ההרשאות חובר בהצלחה")
            self._refresh_credentials_status()
            messagebox.showinfo(APP_TITLE, "קובץ ההרשאות חובר בהצלחה!\nעכשיו אפשר לחבר חשבונות Gmail בלשונית הבאה.")
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"שגיאה בייבוא הקובץ:\n{e}")

    # ---------------- clients tab ----------------
    def _build_clients_tab(self):
        frame = self.clients_tab
        columns = ("name", "email", "notes")
        self.clients_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.clients_tree.heading("name", text="שם")
        self.clients_tree.heading("email", text="אימייל")
        self.clients_tree.heading("notes", text="הערות")
        self.clients_tree.column("name", width=200)
        self.clients_tree.column("email", width=260)
        self.clients_tree.column("notes", width=260)
        self.clients_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="+ הוסף לקוח", command=self._add_client_dialog).pack(side="right")
        ttk.Button(btn_frame, text="הסר לקוח נבחר", command=self._remove_selected_client).pack(side="right", padx=8)

        self._refresh_clients()

    def _refresh_clients(self):
        for row in self.clients_tree.get_children():
            self.clients_tree.delete(row)
        for c in clients_db.load_clients():
            self.clients_tree.insert("", "end", values=(c["name"], c["email"], c.get("notes", "")))

    def _add_client_dialog(self):
        dlg = AddClientDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            name, email, notes = dlg.result
            clients_db.add_client(name, email, notes)
            self._refresh_clients()
            self._log(f"✅ נוסף לקוח: {name} ({email})")

    def _remove_selected_client(self):
        sel = self.clients_tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "בחר לקוח מהרשימה קודם")
            return
        email = self.clients_tree.item(sel[0])["values"][1]
        if messagebox.askyesno(APP_TITLE, f"להסיר את הלקוח עם המייל {email}?"):
            clients_db.remove_client(email)
            self._refresh_clients()
            self._log(f"🗑️ הוסר לקוח: {email}")

    # ---------------- accounts tab ----------------
    def _build_accounts_tab(self):
        frame = self.accounts_tab
        ttk.Label(frame, text="חשבונות Gmail מחוברים לעסק:", font=("", 11, "bold")).pack(
            anchor="e", padx=10, pady=(10, 0)
        )
        self.accounts_listbox = tk.Listbox(frame, height=10)
        self.accounts_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="+ חבר חשבון Gmail", command=self._add_account_dialog).pack(side="right")
        ttk.Button(btn_frame, text="נתק חשבון נבחר", command=self._remove_selected_account).pack(side="right", padx=8)

        self._refresh_accounts()

    def _refresh_accounts(self):
        self.accounts_listbox.delete(0, "end")
        for a in accounts_db.load_accounts():
            self.accounts_listbox.insert("end", a)

    def _add_account_dialog(self):
        if not os.path.exists(self._credentials_path()):
            messagebox.showerror(
                APP_TITLE,
                "עדיין לא חיברת קובץ הרשאות של Google.\n"
                "עבור ללשונית 'הגדרות' וחבר אותו קודם.",
            )
            return

        name = simpledialog.askstring(APP_TITLE, "תן כינוי לחשבון (למשל: מכירות):", parent=self)
        if not name:
            return
        if name in accounts_db.load_accounts():
            messagebox.showwarning(APP_TITLE, f"חשבון בשם '{name}' כבר קיים.")
            return

        accounts_db.add_account(name)
        self._refresh_accounts()
        messagebox.showinfo(
            APP_TITLE,
            f"החשבון '{name}' נוסף.\nעכשיו ייפתח דפדפן - התחבר עם חשבון הג'ימייל הנכון ואשר גישה.",
        )
        threading.Thread(target=self._authenticate_account, args=(name,), daemon=True).start()

    def _authenticate_account(self, name):
        try:
            gmail_client.get_service(name, log=self._log)
            self._log(f"✅ החשבון '{name}' חובר בהצלחה!")
        except Exception as e:
            self._log(f"❌ שגיאה בחיבור החשבון '{name}': {e}")

    def _remove_selected_account(self):
        sel = self.accounts_listbox.curselection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "בחר חשבון מהרשימה קודם")
            return
        name = self.accounts_listbox.get(sel[0])
        if messagebox.askyesno(APP_TITLE, f"לנתק את החשבון '{name}'?"):
            accounts_db.remove_account(name)
            self._refresh_accounts()
            self._log(f"🗑️ נותק חשבון: {name}")

    # ---------------- sync & reports tab ----------------
    def _build_sync_tab(self):
        frame = self.sync_tab
        now = datetime.now()

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=10, pady=15)

        ttk.Label(top, text="שנה:").pack(side="right", padx=(4, 2))
        self.year_var = tk.StringVar(value=str(now.year))
        ttk.Entry(top, textvariable=self.year_var, width=6, justify="center").pack(side="right")

        ttk.Label(top, text="חודש:").pack(side="right", padx=(12, 2))
        self.month_var = tk.StringVar(value=str(now.month))
        ttk.Combobox(
            top, textvariable=self.month_var, values=[str(i) for i in range(1, 13)],
            width=4, state="readonly", justify="center"
        ).pack(side="right")

        ttk.Button(top, text="🔄  סנכרן מה-Gmail", command=self._start_sync).pack(side="left", padx=8)
        ttk.Button(top, text="📄  הפק דוח ופתח", command=self._generate_report).pack(side="left", padx=8)

        ttk.Label(
            frame,
            text="לחצו 'סנכרן' כדי לשלוף מיילים מכל החשבונות המחוברים עבור החודש שנבחר,\n"
                 "ואז 'הפק דוח' כדי ליצור ולפתוח את הדוח החודשי. עדכונים יופיעו ביומן הפעילות למטה.",
            justify="right",
        ).pack(padx=10, anchor="e")

    def _get_selected_period(self):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            if not (1 <= month <= 12):
                raise ValueError
            return year, month
        except ValueError:
            messagebox.showerror(APP_TITLE, "שנה/חודש לא תקינים")
            return None

    def _start_sync(self):
        period = self._get_selected_period()
        if not period:
            return
        year, month = period

        if not clients_db.load_clients():
            messagebox.showwarning(APP_TITLE, "אין לקוחות רשומים. הוסף לקוחות בלשונית 'לקוחות' קודם.")
            return
        if not accounts_db.load_accounts():
            messagebox.showwarning(APP_TITLE, "אין חשבונות Gmail מחוברים. חבר חשבון בלשונית 'חשבונות Gmail' קודם.")
            return

        threading.Thread(target=self._run_sync, args=(year, month), daemon=True).start()

    def _run_sync(self, year, month):
        try:
            self._log(f"מתחיל סנכרון עבור {month:02d}/{year}...")
            sync_mod.sync_all_accounts(year, month, log=self._log)
        except Exception as e:
            self._log(f"❌ שגיאה: {e}")

    def _generate_report(self):
        period = self._get_selected_period()
        if not period:
            return
        year, month = period

        records = report_mod.load_month_data(year, month)
        if not records:
            messagebox.showwarning(
                APP_TITLE, f"אין נתונים שמורים עבור {month:02d}/{year}. יש לסנכרן קודם."
            )
            return
        all_clients = clients_db.load_clients()
        path = report_mod.generate_html_report(year, month, records, all_clients)
        self._log(f"📄 הדוח נוצר: {path}")
        webbrowser.open(f"file://{path}")


def main():
    app = ClientManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
