"""
פתרון למיקום קבצים שעובד גם כשמריצים 'python main.py' וגם כשהתוכנה
ארוזה כקובץ EXE (עם PyInstaller). ב-EXE, קבצים צריכים להישמר ליד ה-EXE
עצמו ולא בתיקייה הזמנית שבה EXE "נפתח" פנימית - זה ה-BASE_DIR הנכון.
"""
import os
import sys


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
