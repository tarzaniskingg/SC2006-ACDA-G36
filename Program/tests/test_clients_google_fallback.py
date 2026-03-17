import os
import sys
import importlib
import unittest


class TestGoogleClientFallback(unittest.TestCase):
    def test_fallback_to_fixture_when_no_key(self):
        # Ensure googlemaps_api is re-imported fresh and fails due to missing key
        os.environ.pop("GOOGLE_MAPS_KEY", None)
        sys.modules.pop("googlemaps_api", None)

        from backend.clients import google as google_client

        routes = google_client.get_directions("A", "B", modes=["transit"], departure_time=None, alternatives=True)
        self.assertIsInstance(routes, list)
        self.assertGreaterEqual(len(routes), 1)
        for r in routes:
            self.assertEqual(r.get("requested_mode"), "transit")


if __name__ == "__main__":
    unittest.main()

