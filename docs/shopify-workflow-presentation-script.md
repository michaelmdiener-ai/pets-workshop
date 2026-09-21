# Shopify Sales and Traffic Reporting Workflow
## Presentation Script

**Audience:** Store owner, developer, or operations handoff recipient  
**Estimated duration:** 8–10 minutes  
**Repository:** `michaelmdiener-ai/pets-workshop`

> **Presenter note:** This script describes the implementation as documented on 21 September 2026. Gmail is the configured notification channel. Slack and generic webhook alerts are designed as the next extension but are not yet enabled in the workflow files.

---

## Slide 1 — Purpose and outcome

### On-slide content

- Automated Shopify sales and traffic reporting
- Daily report delivery by email
- Weekly workflow-health monitoring
- Safe handoff with documented troubleshooting

### Speaker script

“This workflow automates the collection and delivery of Shopify sales and traffic reports for the Scales and tails store. The target outcome is a daily report that runs without manual intervention, a weekly check that confirms the reporting pipeline is healthy, and a clear handoff record for maintaining the system.

The design uses GitHub Actions as the scheduler and execution environment, Shopify’s GraphQL Admin API as the data source, Gmail SMTP for delivery, and GitHub Actions artifacts for temporary report retention.”

### Transition

“Let’s start with the daily path, which is the primary data-collection workflow.”

---

## Slide 2 — Daily reporting schedule

### On-slide content

- Runs daily at **06:00 Africa/Johannesburg**
- Configured as **04:00 UTC**
- Collects the previous 24 hours
- Supports manual `workflow_dispatch`

### Speaker script

“The daily workflow runs at 04:00 UTC, which corresponds to 06:00 in Africa/Johannesburg. Each run calculates a rolling 24-hour reporting window using UTC timestamps. This avoids dependence on the machine’s local timezone and gives each report a consistent time boundary.

The workflow can also be started manually from the GitHub Actions interface. That manual trigger is important for first-time validation, troubleshooting, and confirming a token or app-scope change before waiting for the next scheduled run.”

### Transition

“Once triggered, the workflow collects Shopify data through two related paths.”

---

## Slide 3 — Shopify data collection and report generation

### On-slide content

1. Shopify GraphQL Admin API request
2. ShopifyQL sales and traffic query
3. Direct order query
4. JSON, CSV, and Markdown exports
5. GitHub artifact upload

### Speaker script

“The collector sends a Shopify GraphQL Admin API request using the store domain and Admin API token supplied through GitHub secrets. It attempts a ShopifyQL query for sales, orders, sessions, and conversion-rate metrics, while also querying direct order records.

The collector produces three outputs: a JSON file containing structured results and errors, a CSV file containing order-level data, and a Markdown summary designed for quick human review. These files are uploaded as GitHub Actions artifacts and retained for 30 days.

A key safety rule is that traffic and conversion values are never inferred from order counts. If ShopifyQL cannot return traffic metrics, the report records the limitation rather than presenting an estimate as fact.”

### Transition

“That separation between successful order retrieval and unavailable traffic metrics is central to the failure design.”

---

## Slide 4 — Failure handling in the daily workflow

### On-slide content

- Traffic or metric limitation: record the error and preserve order results
- Critical Shopify API failure: fail the workflow
- Gmail SMTP failure: fail the workflow
- Gmail failure notification: planned and shown in the architecture

### Speaker script

“The daily workflow distinguishes between a partial reporting limitation and a critical execution failure. If ShopifyQL rejects a traffic metric or reports a permission issue, the collector records the error in the JSON and Markdown outputs while preserving any direct order data it successfully obtained.

If the Shopify API cannot authenticate, the required environment variables are missing, or Gmail SMTP cannot send the report, the workflow fails visibly. The Mermaid architecture also shows an automated Gmail failure-notification path for those failures.

The first manual GitHub Actions test demonstrated this behavior: the workflow setup completed, but the report step stopped immediately because the required Shopify and Gmail secrets had not yet been configured. No Shopify request or email was sent in that run.”

### Transition

“The daily report is only half of the operational design. The second workflow checks whether the first one has been healthy over time.”

---

## Slide 5 — Weekly health-check workflow

### On-slide content

- Runs every Monday at **09:00 Africa/Johannesburg**
- Configured as **07:00 UTC**
- Reviews the previous seven days
- Checks run conclusions and artifacts
- Emails a HEALTHY or UNHEALTHY summary

### Speaker script

“The weekly health-check workflow runs every Monday at 07:00 UTC, or 09:00 in Johannesburg. It uses the GitHub API to inspect the previous seven days of daily report workflow runs.

The check counts successful and failed runs, identifies whether the latest run succeeded, and verifies that the latest successful run uploaded report artifacts. It then emails a health summary. A critical finding, such as no runs, a failed latest run, or missing artifacts from a successful run, causes the health-check workflow to fail visibly in GitHub Actions.

This provides an operational signal even when nobody is manually opening the daily report artifacts.”

### Transition

“Both workflows depend on a small, controlled set of secrets.”

---

## Slide 6 — Secrets and security boundaries

### On-slide content

| Secret | Purpose |
|---|---|
| `SHOPIFY_STORE` | Shopify `.myshopify.com` domain |
| `SHOPIFY_ADMIN_TOKEN` | Shopify GraphQL access |
| `GMAIL_USERNAME` | Gmail sending account |
| `GMAIL_APP_PASSWORD` | Gmail SMTP authentication |
| `EMAIL_TO` | Optional configurable recipient |

### Speaker script

“Credentials are kept out of the repository and injected at runtime through GitHub Actions secrets. The Shopify token should have `read_orders` and `read_reports`. Historical orders beyond the standard window may require `read_all_orders` and separate approval.

The Gmail sender requires two-step verification and a Google app password rather than the normal account password. `EMAIL_TO` is optional; when it is absent, the current documented recipient is `michaelmdiener@gmail.com`.

The handoff file explicitly prohibits recording secret values. The repository was scanned for embedded Shopify, Gmail, Slack, and webhook credentials before the documented changes were pushed.”

### Transition

“Permissions are the most likely source of a partial or failed Shopify report, so the handoff includes a defined troubleshooting sequence.”

---

## Slide 7 — Permission troubleshooting path

### On-slide content

1. Check `currentAppInstallation.accessScopes`
2. Confirm `read_orders` and `read_reports`
3. Test a basic `orders` query
4. Test simple ShopifyQL
5. Request protected-data approval if needed
6. Reauthorize and replace the GitHub token

### Speaker script

“The troubleshooting process starts by checking the scopes granted to the installed Shopify app. The first required scopes are `read_orders` and `read_reports`. If customer or historical order data is needed, additional scopes and approvals may apply.

The recommended testing order is deliberate. First test a basic orders query. If that fails, fix `read_orders` before investigating ShopifyQL. Next test a simple query such as `FROM sales SHOW total_sales, orders SINCE -7d`. Only after that succeeds should traffic and conversion metrics be added.

The handoff records the previously observed error that restricted order-access scopes prevented `shopifyqlQuery` from running. It also records the need to reauthorize or reinstall the app after scope changes and then replace the GitHub `SHOPIFY_ADMIN_TOKEN` secret.”

### Transition

“The architecture also includes a local verification layer so code changes can be tested without sending real reports.”

---

## Slide 8 — Local testing and validation

### On-slide content

- Python syntax checks
- Workflow YAML parsing
- Mocked Shopify GraphQL request
- Mocked Gmail SMTP authentication
- Three attachment validation
- No real credentials or email required

### Speaker script

“A reusable offline test was added to the repository. It validates the Shopify GraphQL request URL, token-header handling, order parsing, Gmail SMTP host and port, authentication flow, and creation of the Markdown, JSON, and CSV attachments.

The test uses fake values and mocked network functions, so it does not contact Shopify or send an email. This makes it suitable for pre-push validation. The actual end-to-end test still requires the GitHub repository secrets and a manual workflow run.”

### Transition

“The handoff also captures the current notification expansion plan.”

---

## Slide 9 — Notification architecture and handoff status

### On-slide content

- Gmail: configured channel
- Slack: designed, not yet enabled
- Generic webhook: designed, not yet enabled
- Planned secrets: `SLACK_WEBHOOK_URL`, `FAILURE_WEBHOOK_URL`
- Notification steps should use `continue-on-error: true`

### Speaker script

“Gmail is the active notification channel for reports, health summaries, and the documented failure-notification path. Slack and a generic webhook receiver are the next extension points.

The proposed design adds two repository secrets: `SLACK_WEBHOOK_URL` and `FAILURE_WEBHOOK_URL`. Failure steps would run only after an earlier step fails, include the repository and GitHub run URL, and use `continue-on-error: true`. That last point is important: if Slack or the webhook receiver is unavailable, the notification outage must not obscure the original Shopify or Gmail failure.

At the time of this handoff, those channels are documented as planned but have not been added to the workflow files or delivery-tested.”

### Transition

“Finally, the handoff defines the remaining implementation and verification work.”

---

## Slide 10 — Handoff and next steps

### On-slide content

- Add and verify repository secrets
- Confirm Shopify scopes and approvals
- Run daily workflow manually
- Run weekly health check manually
- Verify report artifacts and Gmail delivery
- Implement and test Slack/webhook notifications
- Monitor scheduled runs

### Speaker script

“The immediate next step is to add the Shopify and Gmail secrets in the repository’s Actions settings, confirm the Shopify scopes, and run the daily workflow manually. The report email and three artifacts should then be checked.

Next, run the weekly health check manually and confirm that it can inspect daily runs and artifacts. After that, implement the Slack and generic webhook steps in both workflows, add their URLs as secrets, and test them using a safe branch or controlled diagnostic failure rather than breaking the production `main` workflow.

The handoff document is the continuity record. It lists the goal, current state, active files, changes made, failed attempts, permission troubleshooting, notification status, and next steps. It deliberately excludes all credential values.”

---

## Closing statement

“This architecture provides a clear separation of responsibilities: Shopify supplies the data, GitHub Actions schedules and executes the workflows, Gmail delivers the reports, GitHub artifacts retain the outputs, and the weekly check monitors operational health. The system is designed to preserve useful order data when traffic reporting is unavailable, fail visibly when the pipeline cannot be trusted, and extend to Slack or generic webhooks without weakening the primary failure signal.”

---

## Reference links

- [Repository](https://github.com/michaelmdiener-ai/pets-workshop)
- [Daily report workflow](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/.github/workflows/shopify-daily-report.yml)
- [Weekly health-check workflow](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/.github/workflows/shopify-weekly-health.yml)
- [Workflow visual](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/docs/shopify-workflow.png)
- [Workflow Mermaid source](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/docs/shopify-workflow.mmd)
- [Handoff document](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/handoff.md)
