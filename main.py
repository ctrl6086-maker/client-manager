"""
ניהול לקוחות + מעקב פעולות מול Gmail + דוח חודשי.

שימוש:
  python main.py add --name "ישראל ישראלי" --email israel@example.com
  python main.py list
  python main.py remove --email israel@example.com

  python main.py add-account --name "מכירות"      # מחבר חשבון גימייל נוסף
  python main.py list-accounts
  python main.py remove-account --name "מכירות"

  python main.py sync                 # שולף מיילים מכל החשבונות המחוברים, לחודש הנוכחי
  python main.py sync --year 2026 --month 7   # חודש ספציפי
  python main.py report               # מפיק דוח מאוחד לחודש הנוכחי (מהנתונים שכבר נאספו)
"""
import argparse
import sys
import webbrowser
from datetime import datetime

import clients as clients_db
import accounts as accounts_db
import report as report_mod
import sync as sync_mod

# תמיכה בעברית ובאימוג'ים גם ב-cmd.exe של ווינדוס
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def cmd_add(args):
    clients_db.add_client(args.name, args.email, args.notes or "")


def cmd_remove(args):
    clients_db.remove_client(args.email)


def cmd_list(args):
    clients_db.list_clients()


def cmd_add_account(args):
    accounts_db.add_account(args.name)


def cmd_remove_account(args):
    accounts_db.remove_account(args.name)


def cmd_list_accounts(args):
    accounts_db.list_accounts()


def cmd_sync(args):
    year = args.year or datetime.now().year
    month = args.month or datetime.now().month
    sync_mod.sync_all_accounts(year, month, log=print)
    print("   כדי להפיק דוח: python main.py report --year {} --month {}".format(year, month))


def cmd_report(args):
    year = args.year or datetime.now().year
    month = args.month or datetime.now().month

    all_clients = clients_db.load_clients()
    records = report_mod.load_month_data(year, month)

    if not records:
        print(f"⚠️  אין נתונים שמורים עבור {month:02d}/{year}. הרץ קודם: python main.py sync --year {year} --month {month}")
        return

    path = report_mod.generate_html_report(year, month, records, all_clients)
    print(f"✅ הדוח נוצר: {path}")
    try:
        webbrowser.open(f"file://{path}")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="ניהול לקוחות ודוח פעולות חודשי מבוסס Gmail")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="הוספת לקוח")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--email", required=True)
    p_add.add_argument("--notes", required=False)
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="הסרת לקוח")
    p_remove.add_argument("--email", required=True)
    p_remove.set_defaults(func=cmd_remove)

    p_list = sub.add_parser("list", help="הצגת רשימת לקוחות")
    p_list.set_defaults(func=cmd_list)

    p_add_acc = sub.add_parser("add-account", help="חיבור חשבון Gmail נוסף")
    p_add_acc.add_argument("--name", required=True, help="כינוי חופשי לחשבון, למשל 'מכירות'")
    p_add_acc.set_defaults(func=cmd_add_account)

    p_remove_acc = sub.add_parser("remove-account", help="ניתוק חשבון Gmail")
    p_remove_acc.add_argument("--name", required=True)
    p_remove_acc.set_defaults(func=cmd_remove_account)

    p_list_acc = sub.add_parser("list-accounts", help="הצגת חשבונות Gmail מחוברים")
    p_list_acc.set_defaults(func=cmd_list_accounts)

    p_sync = sub.add_parser("sync", help="שליפת מיילים מכל חשבונות ה-Gmail עבור חודש")
    p_sync.add_argument("--year", type=int, required=False)
    p_sync.add_argument("--month", type=int, required=False)
    p_sync.set_defaults(func=cmd_sync)

    p_report = sub.add_parser("report", help="הפקת דוח חודשי מהנתונים שנאספו")
    p_report.add_argument("--year", type=int, required=False)
    p_report.add_argument("--month", type=int, required=False)
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"\n❌ שגיאה: {e}")
        if getattr(sys, "frozen", False):
            input("\nלחץ Enter לסגירה...")
        sys.exit(1)


if __name__ == "__main__":
    # אם מפעילים ע"י דאבל-קליק על ה-EXE (בלי פרמטרים בשורת הפקודה),
    # אין טעם לנסות argparse - נציג הודעה ברורה ולא ניתן לחלון להיסגר מיד
    if len(sys.argv) == 1:
        print("=" * 60)
        print("זו תוכנת שורת-פקודה - יש להריץ אותה מתוך cmd/PowerShell")
        print("עם פקודה, לדוגמה:")
        print()
        print("   ClientManager.exe list")
        print("   ClientManager.exe add --name \"שם\" --email \"mail@example.com\"")
        print("   ClientManager.exe sync")
        print("   ClientManager.exe report")
        print()
        print("לרשימת כל הפקודות: ClientManager.exe --help")
        print("=" * 60)
        input("\nלחץ Enter לסגירה...")
        sys.exit(0)

    main()
