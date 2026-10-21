import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from services.pollService import (
    PollError,
    PollService,
    format_duration,
    format_portable_results,
    normalize_builtin_emoji,
    parse_duration,
    parse_portable_duration,
    parse_portable_poll,
)


class PollParsingTests(unittest.TestCase):
    def test_builtin_emoji_shortcodes_are_normalized(self):
        self.assertEqual(normalize_builtin_emoji(":smile:"), "😄")
        self.assertEqual(normalize_builtin_emoji(":thumbsup:"), "👍")
        self.assertEqual(normalize_builtin_emoji(":thumbs_up:"), "👍")

    def test_pasted_unicode_emoji_is_preserved(self):
        self.assertEqual(normalize_builtin_emoji("🔥"), "🔥")

    def test_non_emoji_text_is_rejected(self):
        self.assertIsNone(normalize_builtin_emoji("not-an-emoji"))

    def test_plain_portable_duration_is_minutes(self):
        self.assertEqual(parse_portable_duration("30"), timedelta(minutes=30))

    def test_portable_duration_accepts_case_insensitive_hours_and_days(self):
        self.assertEqual(parse_portable_duration("2H"), timedelta(hours=2))
        self.assertEqual(parse_portable_duration("1d"), timedelta(days=1))

    def test_duration_cannot_exceed_thirty_days(self):
        with self.assertRaisesRegex(PollError, "30 days"):
            parse_duration(31, "days")

    def test_comma_delimited_poll_command(self):
        duration, title, description, options = parse_portable_poll(
            "!poll 30 Who should roll?, Vote for who should roll, Fred, Judy, Bill, Bert, Anna"
        )
        self.assertEqual(duration, timedelta(minutes=30))
        self.assertEqual(title, "Who should roll?")
        self.assertEqual(description, "Vote for who should roll")
        self.assertEqual(options, ("Fred", "Judy", "Bill", "Bert", "Anna"))

    def test_requires_two_options(self):
        with self.assertRaisesRegex(PollError, "at least two"):
            parse_portable_poll("!poll 30 Title, Description, Only one")

    def test_readable_duration(self):
        self.assertEqual(format_duration(timedelta(minutes=90)), "90 minutes")
        self.assertEqual(format_duration(timedelta(hours=2)), "2 hours")

    def test_all_tied_top_results_are_reported(self):
        result = format_portable_results(
            "Choose", ("Fred", "Judy", "Bill"), (1, 2, 1, 2)
        )
        self.assertIn("1-Fred (2 votes)", result)
        self.assertIn("2-Judy (2 votes)", result)
        self.assertNotIn("3-Bill", result)

    def test_no_votes_reports_every_option_as_tied(self):
        result = format_portable_results("Choose", ("Fred", "Judy"), ())
        self.assertIn("1-Fred (0 votes)", result)
        self.assertIn("2-Judy (0 votes)", result)


class PollStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.service = PollService(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def create_poll(self):
        return self.service.create(
            guild_id="1", channel_id="2", creator_id="3", title="Choose",
            description="Pick one", options=("A", "B"), emojis=("🅰️", "🅱️"),
            duration=timedelta(minutes=5), mod_channel_id="4",
        )

    def test_create_delivery_end_and_publish(self):
        poll = self.create_poll()
        self.assertEqual(poll.status, "active")
        poll = self.service.update_delivery(poll.id, message_id="10", mod_message_id="11")
        self.assertEqual(poll.message_id, "10")
        poll = self.service.end(poll.id, [4, 4])
        self.assertEqual(poll.results, [4, 4])
        self.assertEqual(self.service.publish(poll.id).status, "published")

    def test_first_vote_is_locked(self):
        poll = self.create_poll()
        self.assertTrue(self.service.record_vote(poll.id, "user-1", 0))
        self.assertFalse(self.service.record_vote(poll.id, "user-1", 1))
        self.assertEqual(self.service.get(poll.id).votes, {"user-1": 0})

    def test_removing_current_vote_allows_another_selection(self):
        poll = self.create_poll()
        self.assertTrue(self.service.record_vote(poll.id, "user-1", 0))
        self.assertTrue(self.service.remove_vote(poll.id, "user-1", 0))
        self.assertTrue(self.service.record_vote(poll.id, "user-1", 1))
        self.assertEqual(self.service.get(poll.id).votes, {"user-1": 1})

    def test_removing_an_option_not_selected_does_not_clear_vote(self):
        poll = self.create_poll()
        self.service.record_vote(poll.id, "user-1", 0)
        self.assertFalse(self.service.remove_vote(poll.id, "user-1", 1))
        self.assertEqual(self.service.get(poll.id).votes, {"user-1": 0})

    def test_finds_active_poll_by_message(self):
        poll = self.create_poll()
        self.service.update_delivery(poll.id, message_id="123")
        self.assertEqual(self.service.find_active_by_message("123").id, poll.id)

    def test_due_returns_expired_active_poll(self):
        poll = self.create_poll()
        future = datetime.now(timezone.utc) + timedelta(minutes=6)
        self.assertEqual([item.id for item in self.service.due(future)], [poll.id])

    def test_duplicate_emojis_are_rejected(self):
        with self.assertRaisesRegex(PollError, "different emoji"):
            self.service.create(
                guild_id="1", channel_id="2", creator_id="3", title="Choose",
                description="Pick", options=("A", "B"), emojis=("✅", "✅"),
                duration=timedelta(minutes=1),
            )
