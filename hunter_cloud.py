#!/usr/bin/env python3
"""Collect public GitHub bounty mentions and Polymarket market snapshots.

This is a read-only research aid. It does not verify escrow, guarantee payment,
estimate fair value, submit pull requests, place trades, or move funds.
"""

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SEARCH_QUERIES = [
    'is:issue is:open "Bounty $"',
    'is:issue is:open label:"💎 Bounty"',
    'is:issue is:open label:bounty "$"',
    'is:issue is:open "Algora" "$"',
    'is:issue is:open "Polar.sh" "$"',
]

# Extract only an amount visibly associated with bounty/reward language.
# This is still an advertised-text hint, not proof of escrow or payment.
REWARD_PATTERNS = (
    re.compile(
        r"\b(?:bounty|reward|prize|payment)\b[^\n]{0,80}?[$]{1,2}\s*"
        r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"[$]{1,2}\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)[^\n]{0,40}"
        r"\b(?:bounty|reward|prize)\b",
        re.IGNORECASE,
    ),
)


def extract_advertised_reward_amount(text: str) -> float | None:
    """Parse an explicitly labelled amount, without inventing a default."""
    for pattern in REWARD_PATTERNS:
        match = pattern.search(text or "")
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def fetch_bounty_candidates(limit: int = 15) -> list[dict]:
    """Find open issues whose text may mention a bounty or reward."""
    headers = {"User-Agent": "ArgonCandidateRadar/2.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    candidates = []
    seen = set()

    for query in SEARCH_QUERIES:
        url = (
            "https://api.github.com/search/issues?q="
            f"{urllib.parse.quote(query)}&per_page=10"
        )
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))

            for item in data.get("items", []):
                item_id = item.get("id")
                if item_id in seen:
                    continue
                seen.add(item_id)

                title = item.get("title", "")
                body = item.get("body", "") or ""
                repository_url = item.get("repository_url", "")
                repository_name = (
                    "/".join(repository_url.split("/")[-2:])
                    if repository_url
                    else "unknown"
                )
                candidates.append({
                    "id": item_id,
                    "repository": repository_name,
                    "title": title[:120],
                    "advertised_reward_usd": extract_advertised_reward_amount(
                        f"{title}\n{body}"
                    ),
                    "url": item.get("html_url", ""),
                    "updated_at": item.get("updated_at"),
                    "funding_verified": False,
                })
        except Exception as exc:
            print(f"GitHub search warning for {query!r}: {exc}")

    candidates.sort(
        key=lambda item: item["advertised_reward_usd"] or 0,
        reverse=True,
    )
    return candidates[:limit]


def fetch_market_snapshot() -> list[dict]:
    """Read displayed probabilities from active, high-volume Polymarket events."""
    url = (
        "https://gamma-api.polymarket.com/events?"
        "active=true&closed=false&limit=10&order=volume24hr&ascending=false"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "ArgonMarketSnapshot/2.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            events = json.loads(response.read().decode("utf-8"))

        markets = []
        for event in events:
            event_title = event.get("title", "")
            for market in event.get("markets", []):
                raw_prices = market.get("outcomePrices")
                if not raw_prices:
                    continue
                prices = (
                    json.loads(raw_prices)
                    if isinstance(raw_prices, str)
                    else raw_prices
                )
                if not isinstance(prices, list) or not prices:
                    continue
                try:
                    market_probability = float(prices[0])
                except (TypeError, ValueError):
                    continue
                if not 0 <= market_probability <= 1:
                    continue

                markets.append({
                    "event": event_title[:80],
                    "question": str(market.get("question", ""))[:120],
                    "market_probability": market_probability,
                })
        return markets[:6]
    except Exception as exc:
        print(f"Polymarket snapshot warning: {exc}")
        return []


def render_markdown(catalog: dict) -> str:
    timestamp = catalog["timestamp"]
    candidates = catalog["candidates"]
    markets = catalog["market_snapshot"]
    lines = [
        "# CANDIDATE BOUNTY MENTIONS — NOT VERIFIED FUNDING",
        (
            f"**Last scan:** `{timestamp}` | "
            f"**Candidate mentions:** `{len(candidates)}`"
        ),
        "",
        "> Amounts below are parsed from public issue text only. "
        "They are not verified escrow, offers, or payment guarantees.",
        "",
        "| Repository / issue | Advertised amount (unverified) | Source |",
        "| :--- | :---: | :--- |",
    ]
    for candidate in candidates:
        amount = candidate["advertised_reward_usd"]
        amount_text = (
            f"${amount:,.2f}" if amount is not None else "Not parsed"
        )
        lines.append(
            f"| **{candidate['repository']}**: {candidate['title']} "
            f"| {amount_text} | [Open issue]({candidate['url']}) |"
        )

    if markets:
        lines += [
            "",
            "## Polymarket public market snapshot",
            "",
            "> Displayed market prices only; no model forecast, edge estimate, "
            "trading recommendation, or backtest is provided.",
            "",
            "| Event / market | Displayed probability |",
            "| :--- | :---: |",
        ]
        for market in markets:
            lines.append(
                f"| {market['event']} — {market['question']} "
                f"| {market['market_probability'] * 100:.2f}% |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    print("=== ARGON PUBLIC CANDIDATE RADAR ===")
    candidates = fetch_bounty_candidates(limit=12)
    market_snapshot = fetch_market_snapshot()
    timestamp = datetime.now(timezone.utc).isoformat()

    catalog = {
        "node": "BoluS095/argon-autonomous-node",
        "timestamp": timestamp,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "market_snapshot": market_snapshot,
        "funding_verified": False,
        "trading_signal_generated": False,
    }

    with open("live_bounties.json", "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    markdown = render_markdown(catalog)
    with open("LATEST_ESCROW_RADAR.md", "w", encoding="utf-8") as handle:
        handle.write(markdown)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(markdown)

    print(
        f"Collected {len(candidates)} candidate issue mentions and "
        f"{len(market_snapshot)} market observations. "
        "Funding and trading signals were not verified/generated."
    )


if __name__ == "__main__":
    main()
