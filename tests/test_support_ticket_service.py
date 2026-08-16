import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.supportTicketService import (
    SupportTicketError,
    SupportTicketService,
    TicketImage,
    validate_message_link,
)


class SupportTicketServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.service = SupportTicketService(
            {
                "max_open_per_user": 3,
                "max_images": 4,
                "max_image_bytes": 1024 * 1024,
                "max_total_image_bytes": 2 * 1024 * 1024,
            },
            self.root,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_creates_sequential_per_guild_ticket_numbers(self):
        first = self.service.create("42", "7", "This is the first support issue.")
        second = self.service.create("42", "8", "This is the second support issue.")

        self.assertEqual(first.number, "T-000001")
        self.assertEqual(second.number, "T-000002")
        self.assertEqual(self.service.get("42", first.number).opener_id, "7")

    def test_oversized_description_reports_count_limit_and_attachment_option(self):
        service = SupportTicketService(
            {"max_description_length": 100},
            self.root,
        )

        with self.assertRaises(SupportTicketError) as raised:
            service.create("42", "7", "x" * 101)

        message = str(raised.exception)
        self.assertIn("101 characters", message)
        self.assertIn("limit is 100", message)
        self.assertIn("image files", message)

    def test_failed_creation_releases_ticket_number(self):
        failed = self.service.create(
            "42", "7", "This ticket fails during Discord delivery."
        )

        self.service.discard_failed_creation("42", failed.number)
        replacement = self.service.create(
            "42", "8", "This ticket succeeds after the failed attempt."
        )

        self.assertEqual(failed.number, "T-000001")
        self.assertEqual(replacement.number, "T-000001")
        self.assertEqual(len(self.service.list("42")), 1)

    def test_failed_creation_hole_is_reused_after_a_later_ticket(self):
        failed = self.service.create("42", "7", "The first delivery will fail.")
        later = self.service.create("42", "8", "The second delivery succeeds.")

        self.service.discard_failed_creation("42", failed.number)
        replacement = self.service.create("42", "9", "The released number is reused.")

        self.assertEqual(later.number, "T-000002")
        self.assertEqual(replacement.number, "T-000001")

    def test_allows_three_open_tickets_per_user_and_releases_slot_on_close(self):
        tickets = [
            self.service.create("42", "7", f"Support issue number {index} needs help.")
            for index in range(3)
        ]

        with self.assertRaisesRegex(SupportTicketError, "at most 3"):
            self.service.create("42", "7", "A fourth open support issue is blocked.")

        self.service.close("42", tickets[0].number, "99", "canceled", "Duplicate request")
        replacement = self.service.create("42", "7", "A replacement support issue is allowed.")
        self.assertEqual(replacement.number, "T-000004")

    def test_claim_resolve_cancel_and_reopen_transitions_persist(self):
        ticket = self.service.create("42", "7", "The ticket transition needs verification.")
        self.service.update_delivery("42", ticket.number, thread_id="555")
        assigned = self.service.claim("42", ticket.number, "99")
        resolved = self.service.close("42", ticket.number, "99", "resolved", "Configuration corrected")
        reopened = self.service.reopen("42", ticket.number, "100")

        self.assertEqual(assigned.status, "assigned")
        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(resolved.close_note, "Configuration corrected")
        self.assertEqual(resolved.history[-1]["note"], "Configuration corrected")
        self.assertEqual(reopened.status, "open")
        self.assertEqual(reopened.thread_id, "555")
        reloaded = SupportTicketService({}, self.root).get("42", ticket.number)
        self.assertEqual(reloaded.status, "open")
        self.assertEqual(
            [entry["action"] for entry in reloaded.history],
            ["opened", "assigned", "resolved", "reopened"],
        )

    def test_closing_requires_a_brief_note(self):
        ticket = self.service.create("42", "7", "This issue needs a closure note.")
        self.service.claim("42", ticket.number, "99")

        with self.assertRaisesRegex(SupportTicketError, "at least 5"):
            self.service.close("42", ticket.number, "99", "resolved", "no")

        self.assertEqual(self.service.get("42", ticket.number).status, "assigned")

    def test_rejects_cross_guild_and_malformed_message_links(self):
        valid = "https://discord.com/channels/42/100/200"
        self.assertEqual(validate_message_link(valid, "42"), valid)
        for invalid in (
            "https://discord.com/channels/43/100/200",
            "https://example.com/channels/42/100/200",
        ):
            with self.assertRaises(SupportTicketError):
                validate_message_link(invalid, "42")

    def test_image_validation_and_metadata_removal(self):
        source = io.BytesIO()
        exif = Image.Exif()
        exif[0x010E] = "private description"
        Image.new("RGB", (4, 4), "red").save(
            source,
            format="JPEG",
            exif=exif,
        )
        image = TicketImage("proof.jpg", "image/jpeg", source.getvalue())

        self.service.validate_images((image,))
        cleaned = self.service.sanitize_image(image)

        with Image.open(io.BytesIO(cleaned.data)) as opened:
            self.assertFalse(opened.getexif())

    def test_rejects_extension_content_type_mismatch(self):
        image = TicketImage("proof.png", "image/jpeg", b"not-used")
        with self.assertRaisesRegex(SupportTicketError, "extension"):
            self.service.validate_images((image,))

    def test_ticket_persists_uploaded_image_count(self):
        ticket = self.service.create(
            "42",
            "7",
            "This support issue includes several screenshots.",
            image_count=4,
        )

        self.assertEqual(ticket.image_count, 4)
        self.assertEqual(self.service.get("42", ticket.number).image_count, 4)

    def test_reopen_respects_three_active_ticket_limit(self):
        closed = self.service.create(
            "42", "7", "This ticket will be closed before the limit is filled."
        )
        self.service.close("42", closed.number, "99", "canceled", "No longer needed")
        for index in range(3):
            self.service.create(
                "42", "7", f"Another active support issue number {index}."
            )

        with self.assertRaisesRegex(SupportTicketError, "maximum of 3"):
            self.service.reopen("42", closed.number, "99")

    def test_corrupt_store_recovers_from_backup(self):
        first = self.service.create("42", "7", "A support issue creates the initial store.")
        self.service.update_delivery("42", first.number, public_message_id="123")
        path = self.service.path("42")
        path.write_text("{broken", encoding="utf-8")

        recovered = SupportTicketService({}, self.root).get("42", first.number)

        self.assertEqual(recovered.number, first.number)
        self.assertTrue(json.loads(path.read_text(encoding="utf-8"))["tickets"])


if __name__ == "__main__":
    unittest.main()
