# Daily Shopify report automation

The workflow at `.github/workflows/shopify-daily-report.yml` runs every day at **06:00 Africa/Johannesburg** (04:00 UTC), collects the previous 24 hours of Shopify sales and traffic data, emails the report to `michaelmdiener@gmail.com`, and retains the generated files as GitHub Actions artifacts for 30 days.

## Required repository secrets

Add these under **Repository → Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|---|---|
| `SHOPIFY_STORE` | Shopify `*.myshopify.com` domain |
| `SHOPIFY_ADMIN_TOKEN` | Admin API token with `read_orders` and `read_reports` |
| `GMAIL_USERNAME` | Gmail address used to send the report |
| `GMAIL_APP_PASSWORD` | Google 16-character app password, not the normal Gmail password |

The recipient is configured as `michaelmdiener@gmail.com` in the workflow. Change it in the workflow only if the recipient changes.

## Gmail requirements

The sending Gmail account must have two-step verification enabled. Create an app password in the Google Account security settings and use that app password as `GMAIL_APP_PASSWORD`. Do not commit the app password or Shopify token to the repository.

## Shopify requirements

The token should have `read_orders` and `read_reports`. ShopifyQL may additionally require the app to be approved for the applicable protected customer data access. If ShopifyQL is unavailable, the workflow still creates the direct order export and records the reporting error in the Markdown and JSON files.

## Manual test

After adding the secrets, open **Actions → Daily Shopify sales and traffic report → Run workflow**. A successful run sends the email and uploads JSON, CSV, and Markdown artifacts. A failed run normally indicates an invalid secret, a missing Shopify scope, a Gmail app-password/authentication issue, or an unavailable ShopifyQL metric.
