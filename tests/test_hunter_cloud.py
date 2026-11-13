import unittest

from hunter_cloud import extract_advertised_reward_amount, render_markdown


class RewardParsingTests(unittest.TestCase):
    def test_parses_amount_after_bounty_label(self):
        self.assertEqual(
            extract_advertised_reward_amount("Bounty reward: $1,250.50"),
            1250.50,
        )

    def test_parses_repeated_dollar_marker(self):
        self.assertEqual(
            extract_advertised_reward_amount("Bounty Seguro ($$750)"),
            750.0,
        )

    def test_parses_amount_before_reward_label(self):
        self.assertEqual(
            extract_advertised_reward_amount("$250 reward for the fix"),
            250.0,
        )

    def test_does_not_invent_a_default_amount(self):
        self.assertIsNone(
            extract_advertised_reward_amount("Please help fix this issue")
        )

    def test_unrelated_dollar_amount_is_not_treated_as_reward(self):
        self.assertIsNone(
            extract_advertised_reward_amount("Our product costs $99 per month")
        )

    def test_rendered_report_disclaims_unverified_funding(self):
        report = render_markdown({
            "timestamp": "2026-11-13T00:00:00+00:00",
            "candidates": [{
                "repository": "example/project",
                "title": "Add a feature",
                "advertised_reward_usd": 100.0,
                "url": "https://github.com/example/project/issues/1",
            }],
            "market_snapshot": [{
                "event": "Example event",
                "question": "Will it happen?",
                "market_probability": 0.42,
            }],
        })
        self.assertIn("NOT VERIFIED FUNDING", report)
        self.assertIn("unverified", report.lower())
        self.assertIn("no model forecast", report.lower())


if __name__ == "__main__":
    unittest.main()
