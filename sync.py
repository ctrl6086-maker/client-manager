"""
לוגיקת הסנכרון המשותפת: מתחבר לכל חשבונות ה-Gmail, שולף מיילים, מסנן
כפילויות (כשאותו מייל מגיע לכמה חשבונות בעסק, למשל בגלל CC), ושומר
את התוצאה עבור החודש הנבחר. נעשה שימוש בקובץ הזה גם ב-GUI וגם ב-CLI
כדי לא לשכפל לוגיקה.
"""
import gmail_client
import clients as clients_db
import accounts as accounts_db
import report as report_mod


def dedupe_records(records):
    """
    מזהה מיילים שהופיעו ביותר מחשבון אחד (למשל בגלל CC בין חשבונות העסק)
    ומשאיר רק רשומה אחת עבורם - עם ציון בשדה 'also_in' באילו חשבונות
    נוספים הוא הופיע. הזיהוי מתבצע לפי Message-ID (מזהה גלובלי וייחודי
    של המייל שלא משתנה בין תיבות), ובמקרים הנדירים שאין Message-ID -
    לפי שילוב של כתובת+נושא+תאריך.
    """
    seen = {}
    ordered_keys = []
    duplicates_removed = 0

    for r in records:
        key = r.get("message_id") or (r["email"], r["subject"], r["date"])
        if key in seen:
            duplicates_removed += 1
            primary = seen[key]
            if r["account"] not in primary.get("also_in", []) and r["account"] != primary["account"]:
                primary.setdefault("also_in", []).append(r["account"])
            continue
        seen[key] = r
        ordered_keys.append(key)

    deduped = [seen[k] for k in ordered_keys]
    return deduped, duplicates_removed


def sync_all_accounts(year, month, log=print):
    """
    מסנכרן את כל חשבונות ה-Gmail המחוברים עבור חודש נתון, מסנן כפילויות,
    ושומר את התוצאה. מחזיר (deduped_records, duplicates_removed).
    זורק RuntimeError עם הודעה ברורה אם חסרים לקוחות/חשבונות.
    """
    all_clients = clients_db.load_clients()
    if not all_clients:
        raise RuntimeError("אין לקוחות רשומים. הוסף לקוחות קודם.")

    account_names = accounts_db.load_accounts()
    if not account_names:
        raise RuntimeError("אין חשבונות Gmail מחוברים. חבר חשבון קודם.")

    emails = [c["email"] for c in all_clients]
    all_records = []

    for account_name in account_names:
        log(f"🔄 מתחבר ל-Gmail (חשבון: {account_name}) ושולף נתונים עבור {month:02d}/{year}...")
        service = gmail_client.get_service(account_name, log=log)
        records = gmail_client.fetch_messages_for_month(service, year, month, emails, account_name)
        log(f"   ✅ {len(records)} פעולות מחשבון '{account_name}'")
        all_records.extend(records)

    deduped_records, duplicates_removed = dedupe_records(all_records)
    report_mod.save_month_data(year, month, deduped_records)

    log(f"✅ סה\"כ {len(deduped_records)} פעולות ייחודיות עבור {month:02d}/{year}")
    if duplicates_removed:
        log(f"   🧹 הוסרו {duplicates_removed} כפילויות (אותו מייל שהופיע בכמה חשבונות)")

    return deduped_records, duplicates_removed
