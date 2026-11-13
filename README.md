# Argon Public Candidate Radar

[![Scheduled scan](https://github.com/BoluS095/argon-autonomous-node/actions/workflows/autonomous_revenue_hunter.yml/badge.svg)](https://github.com/BoluS095/argon-autonomous-node/actions/workflows/autonomous_revenue_hunter.yml)

A small Python research utility that periodically collects public GitHub issue mentions that may describe bounties and snapshots displayed prices from active Polymarket markets.

## What it currently does

- Searches public GitHub issues using a small set of text queries.
- Extracts an advertised amount only when it appears near explicit bounty/reward language.
- Records candidate issue URLs and update timestamps for manual review.
- Reads displayed probabilities from selected public Polymarket markets.
- Publishes a Markdown run summary and JSON/Markdown artifacts from GitHub Actions.

## Important limitations

- **No funding verification:** an amount found in issue text is not proof of escrow, an active offer, eligibility, acceptance, or payment.
- **No revenue claim:** candidate mentions must be checked manually with the project maintainer and the funding provider.
- **No predictive model:** Polymarket values are displayed market observations. This project does not calculate fair value, alpha, Kelly sizing, or trading recommendations.
- **No trading or payment actions:** the collector does not place orders, move funds, claim bounties, comment on issues, or submit pull requests.
- Search results may include duplicates across separate issues, stale information, or misleading posts. Manual due diligence is required.

## Run locally

Requires Python 3.10+ and the standard library only.

```bash
git clone https://github.com/BoluS095/argon-autonomous-node.git
cd argon-autonomous-node
python -m unittest discover -s tests -v
python hunter_cloud.py
```

An optional `GITHUB_TOKEN` environment variable can increase the GitHub API rate limit. It is read from the environment and is not written to the report.

## GitHub Actions

The workflow runs on a two-hour schedule and can also be started manually. Each run writes a summary and uploads a 14-day JSON/Markdown artifact. It uses read-only repository and issue permissions and does not commit generated reports back to the default branch, so scheduled runs do not create artificial contribution activity.

## Security

Never commit API tokens, private keys, bank details, wallet recovery material, or local-machine identifiers. Use GitHub Actions secrets or local environment variables for credentials. Report suspected credential exposure promptly and rotate actual credentials if they have been exposed.

## License

No license file is currently present. Until an explicit license is added, do not assume this repository grants permission to reuse, modify, or redistribute its code.
