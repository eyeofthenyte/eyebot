import tempfile
import unittest

from services.platformJobService import PlatformJobService


class PlatformJobTests(unittest.TestCase):
    def test_enqueue_claim_complete(self):
        with tempfile.TemporaryDirectory() as root:
            jobs = PlatformJobService(root)
            job_id = jobs.enqueue("42", "bluesky", "post", {"text": "hello"})
            claimed, job = jobs.claim_next("bluesky")
            self.assertEqual(job["id"], job_id)
            self.assertEqual(job["guild_id"], "42")
            jobs.complete(claimed)
            self.assertIsNone(jobs.claim_next("bluesky"))

    def test_failure_retries_then_dead_letters(self):
        with tempfile.TemporaryDirectory() as root:
            jobs = PlatformJobService(root)
            jobs.enqueue("42", "twitter", "post", {"text": "hello"})
            for attempt in range(3):
                claimed, job = jobs.claim_next("twitter")
                jobs.fail(claimed, job, RuntimeError("failed"))
            self.assertIsNone(jobs.claim_next("twitter"))
            self.assertEqual(len(list((jobs.root / "twitter").glob("*.failed"))), 1)


if __name__ == "__main__":
    unittest.main()
