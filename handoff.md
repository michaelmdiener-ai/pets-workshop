# Handoff

## 1. Goal

Set up automatic daily collection and emailing of Shopify sales and traffic reports for the store **Scales and tails**. Reports should run daily at **06:00 Africa/Johannesburg**, use Shopify GraphQL Admin API data, and email the results to **michaelmdiener@gmail.com** through Gmail SMTP. Workflow failures should also support optional Slack and generic webhook notifications.

## 2. Current state

The reporting automation has been added to `michaelmdiener-ai/pets-workshop` and pushed to the `main` branch. The daily workflow is scheduled for **04:00 UTC**, equivalent to 06:00 in Africa/Johannesburg, and also supports manual execution through GitHub Actions. The weekly health-check workflow runs Mondays at **07:00 UTC**, equivalent to 09:00 in Africa/Johannesburg.

The workflows require a Shopify Admin API token with `read_orders` and `read_reports`. ShopifyQL reporting may additionally require protected-customer-data approval. The workflow preserves direct order results when ShopifyQL fails and records permission errors in the JSON and Markdown exports rather than fabricating traffic or conversion values.

Gmail is the configured notification channel. Slack and generic webhook notifications have been designed but are not yet implemented in the workflow files. Their URLs must be added as GitHub repository secrets before those channels can be enabled. The intended behavior is to keep Slack and webhook notification steps non-blocking so a notification outage does not hide the original Shopify or Gmail workflow failure.

The workflow is not fully operational until the required GitHub repository secrets are added and a manual test run succeeds. The current GitHub repository is `michaelmdiener-ai/pets-workshop`.

## 3. Active files

- `.github/workflows/shopify-daily-report.yml` — daily GitHub Actions schedule, environment variables, report execution, Gmail delivery, and artifact upload.
- `.github/workflows/shopify-weekly-health.yml` — weekly run and artifact health check with Gmail summary delivery.
- `scripts/shopify_sales_traffic_report.py` — Shopify GraphQL collector that exports JSON, CSV, and Markdown reports.
- `scripts/run_and_email_shopify_report.py` — runs the collector and emails the report attachments through Gmail SMTP.
- `scripts/check_shopify_workflow_health.py` — checks recent daily workflow runs and artifacts, then emails a health summary.
- `scripts/test_shopify_report_local.py` — offline test for the Shopify GraphQL request shape, order parsing, Gmail SMTP authentication flow, and report attachments.
- `docs/shopify-daily-report.md` — setup instructions, required secrets, Gmail requirements, Shopify scope requirements, and manual testing steps.
- `docs/shopify-workflow.mmd` — Mermaid source for the workflow visual, including Gmail failure-notification paths.
- `docs/shopify-workflow.png` — rendered workflow visual.
- `handoff.md` — this handoff document and the permission and notification troubleshooting record.

## 4. Changes made

- Added the validated Shopify sales and traffic collector to the repository.
- Added a secure Gmail SMTP wrapper using environment variables only.
- Added a GitHub Actions workflow scheduled daily at 04:00 UTC.
- Added a weekly GitHub Actions health-check workflow scheduled Mondays at 07:00 UTC.
- Configured the workflow recipient as `michaelmdiener@gmail.com`, with optional `EMAIL_TO` support documented for configurable delivery.
- Configured the daily workflow to collect the previous 24 hours of data.
- Configured JSON, CSV, and Markdown artifact retention for 30 days.
- Added manual `workflow_dispatch` support to the daily and weekly workflows.
- Added setup documentation and a Mermaid workflow visual.
- Added an offline integration test and verified the Shopify request shape, order parsing, Gmail SMTP flow, and three report attachments without using real credentials or sending email.
- Added documented permission-validation procedures for checking `currentAppInstallation.accessScopes`, testing direct order access, testing ShopifyQL independently, replacing the GitHub `SHOPIFY_ADMIN_TOKEN` secret after reauthorization, and rerunning the workflow.
- Defined the Slack and generic webhook notification design: add `SLACK_WEBHOOK_URL` and `FAILURE_WEBHOOK_URL` as repository secrets, send failure payloads after the Gmail alert path, include the GitHub run URL, and use `continue-on-error: true` on notification steps.
- Validated Python syntax and workflow YAML.
- Checked the repository files for embedded Shopify, Gmail, Slack, or webhook secrets.
- Committed and pushed the automation, workflow visual, and handoff changes to `michaelmdiener-ai/pets-workshop`.

## 5. Failed attempts

- Shopify Analytics dashboard access was blocked by a Cloudflare human-verification screen.
- Shopify GraphQL `shopifyqlQuery` was rejected by the connected built-in connector because the app had restricted order-access scopes. The relevant error was: `Apps with restricted order access scopes cannot use the shopifyqlQuery API`.
- The built-in Shopify connector did not expose a scheduled-report or report-email tool.
- Shopify order, draft-order, abandoned-checkout, and customer checks returned no visible recent records through the accessible endpoints. Standard connector order retrieval is limited to the Manus sales channel.
- The first inventory update request for the fifth product contained malformed tool arguments; it was retried successfully and all five products were verified at 40 units.
- The initial local integration-test harness had a patching error and was corrected; the final offline test passed.
- The first manual GitHub Actions test failed because `SHOPIFY_STORE`, `SHOPIFY_ADMIN_TOKEN`, `GMAIL_USERNAME`, and `GMAIL_APP_PASSWORD` were not configured as repository secrets. No Shopify request was made and no email was sent in that run.
- Slack and generic webhook notifications have not yet been enabled; no webhook delivery test has been performed.
- GitHub repository selection was initially pending; `michaelmdiener-ai/pets-workshop` was selected and used successfully.

## 6. Next steps

1. Add these GitHub repository secrets at [Repository Settings → Secrets and variables → Actions](https://github.com/michaelmdiener-ai/pets-workshop/settings/secrets/actions): `SHOPIFY_STORE`, `SHOPIFY_ADMIN_TOKEN`, `GMAIL_USERNAME`, and `GMAIL_APP_PASSWORD`. Never record their values in this file.
2. Confirm the custom Shopify app includes `read_orders` and `read_reports`. Add `read_all_orders` only if historical orders outside Shopify's standard order window are required.
3. If ShopifyQL or protected customer fields are denied, request the minimum required protected-customer-data approval through the Shopify Partner Dashboard or app configuration process.
4. Reauthorize or reinstall the Shopify app after changing scopes, then replace the GitHub `SHOPIFY_ADMIN_TOKEN` secret with the newly authorized token.
5. Verify granted scopes with the Admin GraphQL query `currentAppInstallation { accessScopes { handle description } }`. Confirm `read_orders` and `read_reports` are present.
6. Test a basic `orders` GraphQL query before testing ShopifyQL. If orders fail, fix `read_orders` first.
7. Test a simple ShopifyQL query such as `FROM sales SHOW total_sales, orders SINCE -7d`. Add traffic metrics only after the basic query succeeds.
8. Add the optional `EMAIL_TO` secret if the report recipient should be configurable instead of using `michaelmdiener@gmail.com`.
9. Add `SLACK_WEBHOOK_URL` for Slack alerts and `FAILURE_WEBHOOK_URL` for a generic receiver such as Zapier, Make, n8n, or a custom API endpoint. Never put either URL directly in YAML or source code.
10. Add non-blocking failure-notification steps to both `.github/workflows/shopify-daily-report.yml` and `.github/workflows/shopify-weekly-health.yml`. Each step should run only when a previous step fails, include the repository and run URL, and use `continue-on-error: true`.
11. Run **Actions → Daily Shopify sales and traffic report → Run workflow** manually. Verify the report email and, after Slack/webhook implementation, verify both additional failure channels using a safe test branch or temporary diagnostic failure rather than breaking `main`.
12. Run **Actions → Weekly Shopify report health check → Run workflow** manually and verify the health summary email, Slack alert, and webhook payload when the health check is intentionally made unhealthy in a safe test context.
13. If ShopifyQL returns a missing-field error, remove unsupported metrics and add them back incrementally. If it returns a permission error, review the exact error, confirm scopes, request any required approval, update the GitHub secret, and rerun the workflow.
14. If Gmail authentication fails, verify two-step verification, regenerate the Gmail app password, update `GMAIL_APP_PASSWORD`, and rerun the workflow.
15. Monitor the scheduled workflows after the first successful daily run. Do not store Shopify tokens, Gmail app passwords, Slack webhook URLs, generic webhook URLs, or other credentials in `handoff.md`.

### Permission troubleshooting reference

| Error | Corrective action |
|---|---|
| `Access denied for orders` | Add or reauthorize `read_orders`. |
| `Apps with restricted order access scopes cannot use the shopifyqlQuery API` | Add and verify `read_reports`, confirm the app type supports ShopifyQL, and request required approval. |
| `Access denied for shopifyqlQuery` | Verify `read_reports`, protected-data approval, and a current supported Admin GraphQL API version. |
| Customer-data access denied | Request only the minimum protected-customer-data access needed. |
| Historical orders unavailable | Request `read_all_orders` alongside `read_orders` if required. |
| ShopifyQL field does not exist | Test a simpler query and remove unsupported metrics. |
| Gmail authentication failure | Regenerate the Gmail app password and update the GitHub secret. |

### Notification reference

| Event | Gmail | Slack | Generic webhook |
|---|---:|---:|---:|
| Daily workflow failure | Existing path | Planned via `SLACK_WEBHOOK_URL` | Planned via `FAILURE_WEBHOOK_URL` |
| Weekly health check unhealthy | Existing path | Planned via `SLACK_WEBHOOK_URL` | Planned via `FAILURE_WEBHOOK_URL` |
| Successful daily report | Yes | No | No |
| Successful weekly health check | Yes | No | No |
