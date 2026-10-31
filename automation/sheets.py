from __future__ import annotations

import csv
from pathlib import Path

from core.config import DATA_DIR, settings

CSV_PATH = DATA_DIR / "hr_results.csv"


def _append_csv(row: list[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["telegram_id", "username", "score", "status", "details"])
        writer.writerow(row)


def save_hr_result(telegram_id: int, username: str | None, score: int, status: str, details: str) -> str:
    row = [str(telegram_id), username or "", str(score), status, details]
    creds = settings.google_sheets_credentials
    sheet_name = settings.google_sheets_spreadsheet
    if creds and sheet_name and Path(creds).exists():
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            credentials = Credentials.from_service_account_file(creds, scopes=scopes)
            client = gspread.authorize(credentials)
            sheet = client.open(sheet_name).sheet1
            sheet.append_row(row, value_input_option="USER_ENTERED")
            return "google_sheets"
        except Exception:
            _append_csv(row)
            return "csv_fallback"
    _append_csv(row)
    return "csv"
