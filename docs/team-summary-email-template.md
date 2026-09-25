# Team Summary Email Template

## Subject

Shopify Reporting Workflow: Architecture, Notifications, and Handoff Summary

## Email body

Hi team,

I’m sharing a presentation script that summarizes the Shopify sales and traffic reporting workflow, its notification architecture, and the current handoff status.

The workflow is designed to collect Shopify sales and traffic data daily at **06:00 Africa/Johannesburg**, generate JSON, CSV, and Markdown reports, email the results through Gmail, and retain the report files as GitHub Actions artifacts. A separate weekly health-check workflow reviews recent daily runs, checks artifact availability, and sends a health summary.

The presentation also covers the Shopify GraphQL and ShopifyQL data paths, GitHub Actions secrets, permission troubleshooting, local validation, failure handling, and the planned extension for Slack and generic webhook notifications. Gmail is currently the configured notification channel. Slack and generic webhook alerts are documented as planned additions and have not yet been enabled or delivery-tested.

Key handoff points include:

- The Shopify Admin API token requires `read_orders` and `read_reports`.
- ShopifyQL traffic reporting may require protected-customer-data approval.
- Report failures and permission limitations are recorded explicitly; traffic and conversion values are never inferred from order counts.
- Credentials must remain in GitHub Actions secrets and must not be stored in source files or handoff documentation.
- The remaining operational work is to configure the repository secrets, complete a successful manual workflow run, and implement and test Slack or webhook failure notifications if those channels are required.

The materials are available here:

- [Presentation script](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/docs/shopify-workflow-presentation-script.md)
- [Workflow visual](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/docs/shopify-workflow.png)
- [Daily report workflow](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/.github/workflows/shopify-daily-report.yml)
- [Weekly health-check workflow](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/.github/workflows/shopify-weekly-health.yml)
- [Handoff document](https://github.com/michaelmdiener-ai/pets-workshop/blob/main/handoff.md)
- [Repository](https://github.com/michaelmdiener-ai/pets-workshop)

Please review the presentation script and handoff document before the next implementation or operations review. In particular, please confirm whether Slack and generic webhook alerts should be enabled in addition to Gmail and identify the preferred receiving channels or endpoints.

Regards,

**[Your name]**
