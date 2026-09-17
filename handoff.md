# Handoff

## 1. Goal

Set up automatic daily collection and emailing of Shopify sales and traffic reports for the store **Scales and tails**. Reports should run daily at **06:00 Africa/Johannesburg**, use Shopify GraphQL Admin API data, and email the results to **michaelmdiener@gmail.com** through Gmail SMTP.

## 2. Current state

The reporting automation has been added to `michaelmdiener-ai/pets-workshop` and pushed to the `main` branch in commit `fd319ef` (`Add daily Shopify sales traffic report workflow`). The workflow is scheduled for **04:00 UTC**, equivalent to 06:00 in Africa/Johannesburg, and also supports manual execution through GitHub Actions.

The workflow is not fully operational until the required GitHub repository secrets are added. Shopify traffic reporting also depends on the Admin API token having working `read_reports` access; ShopifyQL may additionally require the relevant protected-customer-data approval. The workflow records permission failures rather than fabricating traffic or conversion values.

## 3. Active files

- `.github/workflows/shopify-daily-report.yml` — daily GitHub Actions schedule, environment variables, report execution, email delivery, and artifact upload.
- `scripts/shopify_sales_traffic_report.py` — Shopify GraphQL collector that exports JSON, CSV, and Markdown reports.
- `scripts/run_and_email_shopify_report.py` — runs the collector and emails the report attachments through Gmail SMTP.
- `docs/shopify-daily-report.md` — setup instructions, required secrets, Gmail requirements, Shopify scope requirements, and manual testing steps.
- `handoff.md` — this handoff document.

## 4. Changes made

- Added the validated Shopify sales and traffic collector to the repository.
- Added a secure Gmail SMTP wrapper using environment variables only.
- Added a GitHub Actions workflow scheduled daily at 04:00 UTC.
- Configured the workflow recipient as `michaelmdiener@gmail.com`.
- Configured the workflow to collect the previous 24 hours of data.
- Configured JSON, CSV, and Markdown artifact retention for 30 days.
- Added manual `workflow_dispatch` support.
- Added setup documentation.
- Validated Python syntax and workflow YAML.
- Checked the new files for embedded Shopify or Gmail secrets.
- Committed and pushed the changes to `michaelmdiener-ai/pets-workshop`.

## 5. Failed attempts

- Shopify Analytics dashboard access was blocked by a Cloudflare human-verification screen.
- Shopify GraphQL `shopifyqlQuery` was rejected by the connected built-in connector because the app had restricted order-access scopes.
- The built-in Shopify connector did not expose a scheduled-report or report-email tool.
- Shopify order, draft-order, abandoned-checkout, and customer checks returned no visible recent records through the accessible endpoints. Standard connector order retrieval is limited to the Manus sales channel.
- The first inventory update request for the fifth product contained malformed tool arguments; it was retried successfully and all five products were verified at 40 units.
- GitHub repository selection was initially pending; `michaelmdiener-ai/pets-workshop` was selected and used successfully.

## 6. Next steps

1. Add these GitHub repository secrets at [Repository Settings → Secrets and variables → Actions](https://github.com/michaelmdiener-ai/pets-workshop/settings/secrets/actions):
   - `SHOPIFY_STORE`
   - `SHOPIFY_ADMIN_TOKEN`
   - `GMAIL_USERNAME`
   - `GMAIL_APP_PASSWORD`
2. Confirm that the Shopify token has `read_orders` and `read_reports` scopes.
3. Confirm that the Gmail sending account has two-step verification enabled and that the app password is valid.
4. Run **Actions → Daily Shopify sales and traffic report → Run workflow** manually.
5. Verify the email arrives at `michaelmdiener@gmail.com`.
6. Inspect the workflow logs and downloaded artifacts for the first successful run.
7. If ShopifyQL fails, review the JSON and Markdown error fields and obtain the required reporting or protected-data approval.
8. Monitor the scheduled workflow after the first daily run.
