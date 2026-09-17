#!/usr/bin/env python3
import json
import importlib.util
import os
import smtplib
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
collector_spec = importlib.util.spec_from_file_location("shopify_sales_traffic_report", ROOT / "scripts" / "shopify_sales_traffic_report.py")
collector = importlib.util.module_from_spec(collector_spec)
collector_spec.loader.exec_module(collector)

class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode()


def fake_urlopen(request, timeout=0):
    assert request.full_url.endswith("/admin/api/2025-10/graphql.json")
    assert request.get_header("X-shopify-access-token") == "fake-token"
    payload = json.loads(request.data.decode())
    assert "shopifyqlQuery" in payload["query"]
    return FakeResponse({"data": {"shopifyqlQuery": {"parseErrors": [], "tableData": {"columns": [], "rows": []}}}})


with patch.object(collector, "urlopen", fake_urlopen):
    result = collector.fetch_shopifyql("example.myshopify.com", "fake-token", "2025-10", "FROM sales SHOW orders SINCE -1d")
    assert result["data"]["shopifyqlQuery"]["parseErrors"] == []

rows = collector.order_rows({"data": {"orders": {"edges": [{"node": {
    "id": "gid://shopify/Order/1", "name": "#1001", "createdAt": "2026-09-17T04:00:00Z",
    "displayFinancialStatus": "PAID", "displayFulfillmentStatus": "UNFULFILLED",
    "totalPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "ZAR"}},
    "lineItems": {"edges": []}
}}]}}})
assert rows[0]["order_name"] == "#1001"
assert rows[0]["total_sales"] == "100.00"

wrapper_path = ROOT / "scripts" / "run_and_email_shopify_report.py"
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    sent = {}
    fake_run = subprocess.CompletedProcess([], 0, stdout="collector ok\n", stderr="")
    def fake_smtp(host, port, timeout):
        assert host == "smtp.gmail.com" and port == 465
        class SMTP:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def login(self, username, password):
                assert username == "sender@example.com" and password == "fake-app-password"
            def send_message(self, message):
                sent["message"] = message
        return SMTP()
    def fake_subprocess_run(command, env, text, capture_output):
        for name, content in {
            "shopify_sales_traffic_report.md": b"# report",
            "shopify_sales_traffic_report.json": b"{}",
            "shopify_orders.csv": b"order_id\n",
        }.items():
            (out / name).write_bytes(content)
        assert command[0] == os.sys.executable
        return fake_run
    env = {
        "SHOPIFY_STORE": "example.myshopify.com",
        "SHOPIFY_ADMIN_TOKEN": "fake-token",
        "GMAIL_USERNAME": "sender@example.com",
        "GMAIL_APP_PASSWORD": "fake-app-password",
        "EMAIL_TO": "recipient@example.com",
        "REPORT_DIR": str(out),
    }
    with patch.dict(os.environ, env, clear=False), patch.object(subprocess, "run", fake_subprocess_run), patch.object(smtplib, "SMTP_SSL", fake_smtp):
        wrapper_spec = importlib.util.spec_from_file_location("run_and_email_shopify_report", wrapper_path)
        wrapper = importlib.util.module_from_spec(wrapper_spec)
        wrapper_spec.loader.exec_module(wrapper)
        assert wrapper.main() == 0
    message = sent["message"]
    assert message["To"] == "recipient@example.com"
    assert len(list(message.iter_attachments())) == 3

print("Local Shopify GraphQL request and Gmail SMTP attachment tests passed")
