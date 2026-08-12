"""
ניהול מסד הלקוחות - קובץ clients.json פשוט.
"""
import json
import os

from paths import get_base_dir

DB_PATH = os.path.join(get_base_dir(), "clients.json")


def load_clients():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clients(clients):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


def add_client(name, email, notes=""):
    clients = load_clients()
    for c in clients:
        if c["email"].lower() == email.lower():
            print(f"⚠️  לקוח עם המייל {email} כבר קיים ({c['name']}).")
            return
    clients.append({"name": name, "email": email, "notes": notes})
    save_clients(clients)
    print(f"✅ נוסף לקוח: {name} ({email})")


def remove_client(email):
    clients = load_clients()
    new_clients = [c for c in clients if c["email"].lower() != email.lower()]
    if len(new_clients) == len(clients):
        print(f"⚠️  לא נמצא לקוח עם המייל {email}")
        return
    save_clients(new_clients)
    print(f"🗑️  הוסר לקוח עם המייל {email}")


def list_clients():
    clients = load_clients()
    if not clients:
        print("אין לקוחות רשומים עדיין. הוסף עם: python main.py add --name '...' --email '...'")
        return
    print(f"\n📋 {len(clients)} לקוחות:")
    for c in clients:
        note = f" | {c['notes']}" if c.get("notes") else ""
        print(f"  • {c['name']} <{c['email']}>{note}")
    print()


def find_client_by_email(email, clients=None):
    clients = clients if clients is not None else load_clients()
    email = email.lower()
    for c in clients:
        if c["email"].lower() == email:
            return c
    return None
