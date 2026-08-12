"""
חיבור ל-Gmail API - אימות OAuth ושליפת מיילים.
בפעם הראשונה ייפתח דפדפן לאישור הגישה. אחרי זה נשמר טוקן מקומי (token.json)
כדי שלא תצטרך להתחבר שוב בכל פעם.
"""
import os
import base64
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from paths import get_base_dir

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = get_base_dir()
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")


def token_path(account_name):
    return os.path.join(BASE_DIR, f"token_{account_name}.json")


def get_service(account_name, log=print):
    """
    מחזיר Gmail service עבור חשבון ספציפי (מזוהה לפי שם/כינוי שנתת לו).
    לכל חשבון יש קובץ token נפרד (token_<name>.json), אבל כולם משתמשים
    באותו credentials.json (אותו "מפתח אפליקציה").
    log: פונקציית קולבק להדפסת סטטוס (ברירת מחדל: print; ה-GUI מעביר
    כאן פונקציה שכותבת ליומן הפעילות בחלון).
    """
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            "לא נמצא קובץ credentials.json.\n"
            "צריך להוריד אותו מ-Google Cloud Console ולשים בתיקיית התוכנה.\n"
            "ההוראות המלאות נמצאות ב-README.md."
        )

    tpath = token_path(account_name)
    creds = None
    if os.path.exists(tpath):
        creds = Credentials.from_authorized_user_file(tpath, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            log(f"🔐 נא להתחבר עכשיו בדפדפן לחשבון: {account_name}")
            log("   (ודא שאתה מתחבר עם חשבון הג'ימייל הנכון!)")
            creds = flow.run_local_server(port=0)
        with open(tpath, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _get_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_messages_for_month(service, year, month, client_emails, account_name=""):
    """
    שולף מהג'ימייל את כל המיילים שנשלחו/התקבלו החודש הנתון
    מול כל אחת מכתובות הלקוחות שסופקו.
    מחזיר רשימת רשומות: {email, direction, subject, date, account}
    """
    start = f"{year}/{month:02d}/01"
    if month == 12:
        end_year, end_month = year + 1, 1
    else:
        end_year, end_month = year, month + 1
    end = f"{end_year}/{end_month:02d}/01"

    results = []
    for client_email in client_emails:
        query = f"(from:{client_email} OR to:{client_email}) after:{start} before:{end}"
        page_token = None
        while True:
            resp = service.users().messages().list(
                userId="me", q=query, pageToken=page_token, maxResults=500
            ).execute()
            for msg_meta in resp.get("messages", []):
                msg = service.users().messages().get(
                    userId="me", id=msg_meta["id"],
                    format="metadata", metadataHeaders=["From", "To", "Subject", "Date", "Message-ID"]
                ).execute()
                headers = msg["payload"]["headers"]
                from_addr = _get_header(headers, "From")
                subject = _get_header(headers, "Subject")
                date_str = _get_header(headers, "Date")
                message_id = _get_header(headers, "Message-ID")
                direction = "נשלח" if client_email.lower() not in from_addr.lower() else "התקבל"
                results.append({
                    "email": client_email,
                    "direction": direction,
                    "subject": subject,
                    "date": date_str,
                    "account": account_name,
                    "msg_id": msg_meta["id"],
                    "message_id": message_id,
                })
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    return results
