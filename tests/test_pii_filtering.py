import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

from gtm_agent import gtm_agent
from gtm_agent import gtm_records


PII_KEYS = {"billing_qualification", "tax_id", "date_of_birth", "card_on_file", "credit_check_ref"}


def serialized(value):
    return json.dumps(value)


class ProspectPIIFilteringTest(unittest.TestCase):
    def setUp(self):
        gtm_agent.data_service._PROFILES.clear()

    def test_prospect_tools_exclude_billing_pii(self):
        for prospect_id in gtm_records.PROSPECTS:
            contact = gtm_agent.get_prospect.invoke({"prospect_id": prospect_id})
            profile = gtm_agent.build_prospect_profile.invoke({"prospect_id": prospect_id})

            self.assertTrue(PII_KEYS.isdisjoint(serialized(contact)))
            self.assertTrue(PII_KEYS.isdisjoint(serialized(profile)))

    def test_score_prospect_excludes_billing_pii_from_scoring_payload(self):
        captured_messages = []

        class FakeScoringLLM:
            def invoke(self, messages):
                captured_messages.append(messages)
                return SimpleNamespace(model_dump=lambda: {"score": 1})

        offering = next(iter(gtm_records.OFFERINGS.values()))
        with patch.object(gtm_agent, "_scoring_llm", FakeScoringLLM()):
            for prospect_id in gtm_records.PROSPECTS:
                profile = gtm_agent.build_prospect_profile.invoke({"prospect_id": prospect_id})
                profile["billing_qualification"] = gtm_records.PROSPECTS[prospect_id]["billing_qualification"]
                gtm_agent.score_prospect.invoke({"prospect_profile": profile, "offering": offering})

        self.assertEqual(len(captured_messages), len(gtm_records.PROSPECTS))
        for messages in captured_messages:
            self.assertTrue(PII_KEYS.isdisjoint(serialized(messages)))


if __name__ == "__main__":
    unittest.main()
