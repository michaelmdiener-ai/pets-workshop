#!/usr/bin/env python3
"""Check recent Shopify report workflow runs and email a health summary."""

from __future__ import annotations

import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO = os.environ.get("GITHUB_REPOSITORY", "michaelmdiener-ai/pets-workshop")
WORKFLOW = os.environ.get("REPORT_WORKFLOW", "shopify-daily-report.yml")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def github_get(path: str) -> dict:
    if not GITHUB_TOKEN:
        raise RuntimeError("Missing GITHUB_TOKEN")
    request = Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "shopify-workflow-health-check/1.0",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API HTTP {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub API network error: {exc.reason}") from exc


def main() -> int:
    username = required("GMAIL_USERNAME")
    app_password = required("GMAIL_APP_PASSWORD")
    recipient = required("EMAIL_TO")
    run_url = f"https://github.com/{REPO}/actions/workflows/{WORKFLOW}"
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")

    runs_payload = github_get(f"/repos/{REPO}/actions/workflows/{WORKFLOW}/runs?per_page=20&created=%3E%3D{since}")
    runs = runs_payload.get("workflow_runs", [])
    findings: list[str] = []
    if not runs:
        findings.append("CRITICAL: No daily report workflow runs were found in the last 7 days.")

    successful = [run for run in runs if run.get("conclusion") == "success"]
    failed = [run for run in runs if run.get("conclusion") not in ("success", "skipped", None)]
    latest = runs[0] if runs else None
    if latest and latest.get("conclusion") != "success":
        findings.append(f"CRITICAL: Latest daily report run concluded {latest.get('conclusion')}.")
    if failed:
        findings.append(f"WARNING: {len(failed)} daily report run(s) failed in the last 7 days.")

    artifact_count = 0
    artifact_names: list[str] = []
    if latest:
        artifacts = github_get(f"/repos/{REPO}/actions/runs/{latest['id']}/artifacts").get("artifacts", [])
        artifact_count = len(artifacts)
        artifact_names = [item.get("name", "(unnamed)") for item in artifacts]
        if latest.get("conclusion") == "success" and not artifacts:
            findings.append("CRITICAL: Latest successful run has no uploaded report artifacts.")

    if not findings:
        findings.append("OK: Daily Shopify report workflow and recent artifacts look healthy.")

    status = "HEALTHY" if not any(item.startswith("CRITICAL") for item in findings) else "UNHEALTHY"
    lines = [
        f"Shopify daily report health: {status}",
        "",
        f"Repository: {REPO}",
        f"Workflow: {WORKFLOW}",
        f"Window: last 7 days since {since}",
        f"Runs found: {len(runs)}",
        f"Successful runs: {len(successful)}",
        f"Failed runs: {len(failed)}",
        f"Latest run: {latest.get('conclusion') if latest else 'none'}",
        f"Latest run URL: {latest.get('html_url') if latest else run_url}",
        f"Latest artifact count: {artifact_count}",
        f"Latest artifacts: {', '.join(artifact_names) if artifact_names else 'none'}",
        "",
        "Findings:",
        *[f"- {item}" for item in findings],
        "",
        "Review workflow:",
        run_url,
    ]
    body = "\n".join(lines)

    message = EmailMessage()
    message["Subject"] = f"Shopify workflow health: {status}"
    message["From"] = username
    message["To"] = recipient
    message.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=45) as smtp:
        smtp.login(username, app_password)
        smtp.send_message(message)

    print(body)
    return 0 if status == "HEALTHY" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
