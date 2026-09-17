#!/usr/bin/env python3
"""Run the Shopify report collector and email its JSON, CSV, and Markdown files.

Credentials are read only from environment variables:
  SHOPIFY_STORE, SHOPIFY_ADMIN_TOKEN
  GMAIL_USERNAME, GMAIL_APP_PASSWORD, EMAIL_TO
"""

from __future__ import annotations

import mimetypes
import os
import smtplib
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts" / "shopify_sales_traffic_report.py"


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    output_dir = Path(os.environ.get("REPORT_DIR", str(ROOT / "reports")))
    output_dir.mkdir(parents=True, exist_ok=True)

    # The collector's output is intentionally kept in a date-specific folder by
    # the workflow. This wrapper only consumes files produced by that run.
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, str(COLLECTOR), "--out-dir", str(output_dir)],
        env=env,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Shopify collector failed with exit code {result.returncode}")

    username = required("GMAIL_USERNAME")
    app_password = required("GMAIL_APP_PASSWORD")
    recipient = required("EMAIL_TO")
    sender_name = os.environ.get("EMAIL_SENDER_NAME", "Shopify Daily Report")

    attachments = [
        output_dir / "shopify_sales_traffic_report.md",
        output_dir / "shopify_sales_traffic_report.json",
        output_dir / "shopify_orders.csv",
    ]
    missing = [str(path) for path in attachments if not path.is_file()]
    if missing:
        raise RuntimeError("Expected report files are missing: " + ", ".join(missing))

    message = EmailMessage()
    message["Subject"] = "Daily Shopify sales and traffic report"
    message["From"] = f"{sender_name} <{username}>"
    message["To"] = recipient
    message.set_content(
        "Attached are the latest Shopify sales and traffic report exports.\n\n"
        "Traffic and conversion fields are included only when ShopifyQL returns them; "
        "the report records any API permission or availability limitations."
    )

    for path in attachments:
        mime_type, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        message.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=45) as smtp:
        smtp.login(username, app_password)
        smtp.send_message(message)
    print(f"Report emailed to {recipient}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
