import tempfile
import unittest

from services.platformJobService import DuplicateJobError, PlatformJobService


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

    def test_idempotency_key_rejects_duplicate_job(self):
        with tempfile.TemporaryDirectory() as root:
            jobs = PlatformJobService(root)
            jobs.enqueue(
                "42",
                "twitter",
                "post",
                {"text": "hello"},
                idempotency_key="42:100:twitter",
                source_message_id="100",
            )
            with self.assertRaises(DuplicateJobError):
                jobs.enqueue(
                    "42",
                    "twitter",
                    "post",
                    {"text": "hello"},
                    idempotency_key="42:100:twitter",
                    source_message_id="100",
                )

    def test_cancel_pending_removes_only_matching_message(self):
        with tempfile.TemporaryDirectory() as root:
            jobs = PlatformJobService(root)
            jobs.enqueue(
                "42", "twitter", "post", {"text": "one"}, source_message_id="100"
            )
            jobs.enqueue(
                "42", "twitter", "post", {"text": "two"}, source_message_id="200"
            )
            removed = jobs.cancel_pending("42", "100")
            self.assertEqual(len(removed), 1)
            jobs.enqueue(
                "42",
                "twitter",
                "post",
                {"text": "replacement"},
                idempotency_key="42:100:twitter",
                source_message_id="100",
            )
            remaining = set()
            for _ in range(2):
                claimed, job = jobs.claim_next("twitter")
                remaining.add(job["source_message_id"])
                jobs.complete(claimed)
            self.assertEqual(remaining, {"100", "200"})


if __name__ == "__main__":
    unittest.main()
