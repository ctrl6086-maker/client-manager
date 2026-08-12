"""
יצירת דוח חודשי (HTML) לפי נתוני הפעולות שנאספו.
"""
import os
import json
from datetime import datetime
from collections import defaultdict

from paths import get_base_dir

BASE_DIR = get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

HEBREW_MONTHS = [
    "", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
    "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
]


def data_path(year, month):
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{year}-{month:02d}.json")


def save_month_data(year, month, records):
    with open(data_path(year, month), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_month_data(year, month):
    path = data_path(year, month)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_html_report(year, month, records, clients):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    email_to_name = {c["email"].lower(): c["name"] for c in clients}

    by_client = defaultdict(list)
    for r in records:
        by_client[r["email"]].append(r)

    total_actions = len(records)
    month_name = HEBREW_MONTHS[month]

    accounts_used = sorted({r.get("account", "") for r in records if r.get("account")})

    rows = ""
    for email, recs in sorted(by_client.items(), key=lambda x: -len(x[1])):
        name = email_to_name.get(email.lower(), email)
        by_account = defaultdict(int)
        for r in recs:
            by_account[r.get("account", "")] += 1
        breakdown = " · ".join(f"{acc}: {cnt}" for acc, cnt in by_account.items() if acc)
        rows += f"""
        <tr>
          <td>{name}</td>
          <td>{email}</td>
          <td class="count">{len(recs)}</td>
          <td class="breakdown">{breakdown}</td>
        </tr>"""

    details = ""
    for email, recs in by_client.items():
        name = email_to_name.get(email.lower(), email)
        items = ""
        for r in recs:
            also_in = r.get("also_in") or []
            shared_tag = f"<span class='shared-tag'>גם ב: {', '.join(also_in)}</span>" if also_in else ""
            items += (
                f"<li><b>{r['direction']}</b> — {r['subject'] or '(ללא נושא)'} "
                f"<span class='date'>{r['date']}</span>"
                f"<span class='account-tag'>{r.get('account','')}</span>"
                f"{shared_tag}</li>"
            )
        details += f"<h3>{name}</h3><ul>{items}</ul>"

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>דוח חודשי - {month_name} {year}</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; color: #222; }}
  h1 {{ color: #2c3e50; }}
  .summary {{ background: #f4f6f8; padding: 16px 20px; border-radius: 8px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 32px; }}
  th, td {{ padding: 10px 12px; border-bottom: 1px solid #e0e0e0; text-align: right; }}
  th {{ background: #2c3e50; color: white; }}
  .count {{ font-weight: bold; color: #2c3e50; }}
  ul {{ margin-top: 4px; }}
  li {{ margin-bottom: 4px; }}
  .date {{ color: #888; font-size: 0.85em; }}
  .breakdown {{ color: #666; font-size: 0.85em; }}
  .account-tag {{ background:#eef1f4; color:#555; font-size:0.75em; border-radius:4px; padding:1px 6px; margin-right:6px; }}
  .shared-tag {{ background:#fff3cd; color:#856404; font-size:0.75em; border-radius:4px; padding:1px 6px; margin-right:6px; }}
</style>
</head>
<body>
  <h1>📊 דוח פעולות חודשי — {month_name} {year}</h1>
  <div class="summary">
    <strong>סה"כ פעולות (מיילים) החודש:</strong> {total_actions}<br>
    <strong>מספר לקוחות פעילים:</strong> {len(by_client)}<br>
    <strong>חשבונות שנכללו בדוח:</strong> {', '.join(accounts_used) if accounts_used else '—'}
  </div>

  <h2>סיכום לפי לקוח (מאוחד משלושת החשבונות)</h2>
  <table>
    <tr><th>לקוח</th><th>מייל</th><th>סה"כ פעולות</th><th>פילוח לפי חשבון</th></tr>
    {rows}
  </table>

  <h2>פירוט</h2>
  {details}

  <p style="color:#999; font-size:0.8em;">נוצר אוטומטית ב-{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</body>
</html>"""

    out_path = os.path.join(REPORTS_DIR, f"report-{year}-{month:02d}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
