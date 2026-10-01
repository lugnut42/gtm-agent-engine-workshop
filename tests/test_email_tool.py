import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import send_prospect_email


class SendProspectEmailTests(unittest.TestCase):
    runtime = SimpleNamespace(config={"metadata": {"user_id": "rep_amills"}})

    def test_disqualified_prospect_is_blocked(self):
        result = send_prospect_email.func(
            {"prospect_id": "LEAD-50001", "email": "spoofed@example.com"},
            "Book a demo",
            "Let us connect.",
            self.runtime,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("disqualified", result["error"])

    def test_qualified_prospect_is_sent_with_source_contact(self):
        result = send_prospect_email.func(
            {
                "prospect_id": "LEAD-12853",
                "name": "Spoofed Name",
                "email": "spoofed@example.com",
            },
            "Book a demo",
            "Let us connect.",
            self.runtime,
        )

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["to"], "omar.okafor@lakesideanalytics.com")
        self.assertEqual(result["to_name"], "Omar Okafor")

    def test_missing_source_record_is_not_sent(self):
        with patch("gtm_agent.gtm_agent.data_service.get_prospect_record", return_value=None):
            result = send_prospect_email.func(
                {"prospect_id": "LEAD-UNKNOWN", "email": "unknown@example.com"},
                "Book a demo",
                "Let us connect.",
                self.runtime,
            )

        self.assertEqual(result, {
            "status": "failed",
            "error": "Prospect record not found; email not sent.",
            "to": "unknown@example.com",
        })


if __name__ == "__main__":
    unittest.main()
