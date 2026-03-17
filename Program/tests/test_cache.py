import unittest
import time

from backend.services.caching import TTLCache


class TestTTLCache(unittest.TestCase):
    def test_status_and_expiry(self):
        c = TTLCache()
        # set realtime item with ttl 1 and force expiration
        item1 = c.set("k1", value={"v": 1}, ttl_sec=1, source="realtime")
        item1.retrieved_at = time.time() - 10
        status = c.status()
        self.assertIn("k1", status)
        self.assertTrue(status["k1"]["is_fallback"])  # expired => fallback

        # set fallback-sourced item not expired: still marked as fallback
        item2 = c.set("k2", value={"v": 2}, ttl_sec=300, source="fallback")
        status = c.status()
        self.assertTrue(status["k2"]["is_fallback"])  # source indicates fallback


if __name__ == "__main__":
    unittest.main()

