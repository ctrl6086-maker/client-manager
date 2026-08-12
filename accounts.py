"""
ניהול רשימת חשבונות ה-Gmail של העסק (accounts.json).
כל חשבון מזוהה בעזרת שם/כינוי חופשי (למשל "מכירות", "תמיכה", "כללי").
"""
import json
import os

from paths import get_base_dir

DB_PATH = os.path.join(get_base_dir(), "accounts.json")


def load_accounts():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_accounts(accounts):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)


def add_account(name):
    accounts = load_accounts()
    if name in accounts:
        print(f"⚠️  חשבון בשם '{name}' כבר קיים.")
        return
    accounts.append(name)
    save_accounts(accounts)
    print(f"✅ נוסף חשבון: {name}")
    print(f"   בפעם הבאה שתריץ 'sync' תתבקש להתחבר לחשבון הזה בדפדפן.")


def remove_account(name):
    accounts = load_accounts()
    if name not in accounts:
        print(f"⚠️  לא נמצא חשבון בשם '{name}'")
        return
    accounts.remove(name)
    save_accounts(accounts)
    token_file = os.path.join(get_base_dir(), f"token_{name}.json")
    if os.path.exists(token_file):
        os.remove(token_file)
    print(f"🗑️  הוסר חשבון: {name}")


def list_accounts():
    accounts = load_accounts()
    if not accounts:
        print("אין חשבונות רשומים עדיין. הוסף עם: python main.py add-account --name 'מכירות'")
        return
    print(f"\n📧 {len(accounts)} חשבונות מחוברים:")
    for a in accounts:
        print(f"  • {a}")
    print()
