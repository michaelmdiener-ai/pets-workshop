#!/usr/bin/env python3
"""Fetch Shopify sales and traffic analytics through the Admin GraphQL API.

Required environment variables:
  SHOPIFY_STORE        e.g. scales-and-tails.myshopify.com
  SHOPIFY_ADMIN_TOKEN  Admin API token; never commit or print this value

Optional:
  SHOPIFY_API_VERSION  Defaults to 2025-10
  SHOPIFY_SINCE        ISO date/time, defaults to 7 days ago (UTC)
  SHOPIFY_UNTIL        ISO date/time, defaults to now (UTC)

The script first runs ShopifyQL. If ShopifyQL is unavailable because of
permissions or unsupported metrics, it still exports a direct orders report.
Traffic fields are never inferred from orders.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_VERSION = "2025-10"
DEFAULT_SHOPIFYQL = (
    "FROM sales SHOW total_sales, orders, sessions, conversion_rate "
    "SINCE {since} UNTIL {until}"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def date_value(value: str) -> str:
    return value.replace("+00:00", "Z")


def graphQL(store: str, token: str, api_version: str, query: str) -> dict[str, Any]:
    url = f"https://{store}/admin/api/{api_version}/graphql.json"
    body = json.dumps({"query": query}).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Shopify-Access-Token": token,
            "User-Agent": "shopify-sales-traffic-report/1.0",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Shopify HTTP {exc.code}: {detail[:1000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error contacting Shopify: {exc.reason}") from exc


def fetch_shopifyql(store: str, token: str, version: str, ql: str) -> dict[str, Any]:
    escaped = json.dumps(ql)
    query = (
        "query { shopifyqlQuery(query: "
        f"{escaped}"
        ") { parseErrors tableData { columns { name dataType displayName } rows } } }"
    )
    return graphQL(store, token, version, query)


def fetch_orders(store: str, token: str, version: str, since: str) -> dict[str, Any]:
    query = """query($query: String!) {
      orders(first: 250, query: $query, sortKey: CREATED_AT, reverse: true) {
        edges { node {
          id name createdAt displayFinancialStatus displayFulfillmentStatus
          totalPriceSet { shopMoney { amount currencyCode } }
          lineItems(first: 100) { edges { node {
            title quantity sku product { id title }
          } } }
        } }
      }
    }"""
    # The generic connector used in this script accepts a raw query. Keep the
    # filter conservative and let Shopify validate the date syntax.
    query = query.replace("query($query: String!)", "query")
    query = query.replace("orders(first: 250, query: $query", f'orders(first: 250, query: "created_at:>={since}"')
    return graphQL(store, token, version, query)


def errors(payload: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for item in payload.get("errors", []) or []:
        result.append(item.get("message", str(item)))
    result.extend(payload.get("data", {}).get("shopifyqlQuery", {}).get("parseErrors", []) or [])
    return result


def order_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    edges = payload.get("data", {}).get("orders", {}).get("edges", []) or []
    rows: list[dict[str, Any]] = []
    for edge in edges:
        node = edge.get("node", {})
        money = node.get("totalPriceSet", {}).get("shopMoney", {})
        products = []
        for line in node.get("lineItems", {}).get("edges", []) or []:
            item = line.get("node", {})
            products.append({"title": item.get("title"), "sku": item.get("sku"), "quantity": item.get("quantity")})
        rows.append({
            "order_id": node.get("id"),
            "order_name": node.get("name"),
            "created_at": node.get("createdAt"),
            "financial_status": node.get("displayFinancialStatus"),
            "fulfillment_status": node.get("displayFulfillmentStatus"),
            "total_sales": money.get("amount"),
            "currency": money.get("currencyCode"),
            "line_items": json.dumps(products, ensure_ascii=False),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0].keys()) if rows else ["order_id", "order_name", "created_at", "financial_status", "fulfillment_status", "total_sales", "currency", "line_items"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    ql = report["shopifyql"]
    traffic = "Unavailable"
    if ql.get("rows"):
        traffic = "Returned by ShopifyQL; see raw JSON for the exact columns and values."
    lines = [
        "# Shopify Sales and Traffic Report",
        "",
        f"**Store:** `{report['store']}`  ",
        f"**Window:** `{report['since']}` to `{report['until']}`  ",
        "",
        "## Summary",
        "",
        f"- Orders returned: **{len(report['orders'])}**",
        f"- Sales rows returned by ShopifyQL: **{len(ql.get('rows', []))}**",
        f"- Traffic/session data: **{traffic}**",
        "",
        "## ShopifyQL status",
        "",
    ]
    if ql.get("errors"):
        lines.extend(["ShopifyQL did not return report data:", "", *[f"> {e}" for e in ql["errors"]], ""])
    else:
        lines.extend(["ShopifyQL returned data successfully. See the JSON export for typed columns and complete rows.", ""])
    lines.extend(["## Orders", "", "| Order | Created | Financial status | Total |", "|---|---|---|---:|"])
    for row in report["orders"]:
        lines.append(f"| {row.get('order_name') or row.get('order_id')} | {row.get('created_at')} | {row.get('financial_status')} | {row.get('total_sales')} {row.get('currency') or ''} |")
    if not report["orders"]:
        lines.append("| None returned | — | — | — |")
    lines.extend(["", "## Limitations", "", "Traffic is reported only when ShopifyQL returns valid session or traffic metrics. The script never estimates sessions or conversion rates from order counts. `read_reports` is required for ShopifyQL, and order data may also require appropriate order/protected-data access.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=".", help="Directory for JSON, CSV, and Markdown exports")
    parser.add_argument("--shopifyql", default=None, help="Override the ShopifyQL query")
    args = parser.parse_args()

    store = os.environ.get("SHOPIFY_STORE", "").strip().replace("https://", "").rstrip("/")
    token = os.environ.get("SHOPIFY_ADMIN_TOKEN", "").strip()
    version = os.environ.get("SHOPIFY_API_VERSION", DEFAULT_API_VERSION).strip()
    if not store or not token:
        print("Missing SHOPIFY_STORE or SHOPIFY_ADMIN_TOKEN environment variable.", file=sys.stderr)
        return 2

    now = utc_now()
    since = date_value(os.environ.get("SHOPIFY_SINCE", (now - timedelta(days=7)).isoformat()))
    until = date_value(os.environ.get("SHOPIFY_UNTIL", now.isoformat()))
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ql = args.shopifyql or DEFAULT_SHOPIFYQL.format(since=since[:10], until=until[:10])
    ql_payload = fetch_shopifyql(store, token, version, ql)
    ql_result = ql_payload.get("data", {}).get("shopifyqlQuery", {}) or {}
    ql_errors = errors(ql_payload)
    ql_rows = ql_result.get("tableData", {}).get("rows", []) if not ql_errors else []
    ql_columns = ql_result.get("tableData", {}).get("columns", []) if not ql_errors else []

    order_payload = fetch_orders(store, token, version, since)
    order_errors = errors(order_payload)
    orders = order_rows(order_payload) if not order_errors else []

    report = {
        "generated_at": now.isoformat(),
        "store": store,
        "api_version": version,
        "since": since,
        "until": until,
        "shopifyql_query": ql,
        "shopifyql": {"columns": ql_columns, "rows": ql_rows, "errors": ql_errors},
        "orders": orders,
        "order_errors": order_errors,
    }
    (out_dir / "shopify_sales_traffic_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(out_dir / "shopify_orders.csv", orders)
    write_markdown(out_dir / "shopify_sales_traffic_report.md", report)

    print(f"Wrote {out_dir / 'shopify_sales_traffic_report.json'}")
    print(f"Wrote {out_dir / 'shopify_orders.csv'}")
    print(f"Wrote {out_dir / 'shopify_sales_traffic_report.md'}")
    if ql_errors:
        print("ShopifyQL errors:", file=sys.stderr)
        for item in ql_errors:
            print(f"- {item}", file=sys.stderr)
    if order_errors:
        print("Order query errors:", file=sys.stderr)
        for item in order_errors:
            print(f"- {item}", file=sys.stderr)
    return 0 if not order_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
