import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile


class UpdateProspectInfoTests(unittest.TestCase):
    def test_update_persists_and_invalidates_profile_cache(self):
        prospect_id = "LEAD-71001"
        record = data_service.PROSPECTS[prospect_id]
        original_tech_stack = list(record["tech_stack"])

        try:
            data_service._PROFILES.pop(prospect_id, None)
            initial = build_prospect_profile.invoke({"prospect_id": prospect_id})
            self.assertNotIn("Kafka", initial["prospect_profile"]["tech_stack"])

            result = data_service.update_prospect_info(prospect_id, "Kafka")

            self.assertEqual(result["tech_stack"], record["tech_stack"])
            self.assertTrue(result["updated"])
            self.assertIn("Kafka", data_service.fetch_tech_stack(prospect_id))

            rebuilt = build_prospect_profile.invoke({"prospect_id": prospect_id})
            self.assertIn("Kafka", rebuilt["prospect_profile"]["tech_stack"])

            duplicate = data_service.update_prospect_info(prospect_id, "Kafka")
            self.assertFalse(duplicate["updated"])
            self.assertEqual(duplicate["tech_stack"].count("Kafka"), 1)
        finally:
            record["tech_stack"] = original_tech_stack
            data_service._PROFILES.pop(prospect_id, None)


if __name__ == "__main__":
    unittest.main()
