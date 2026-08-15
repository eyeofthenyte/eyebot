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

        self.assertEqual(first.number, "TICKET-000001")
        self.assertEqual(second.number, "TICKET-000002")
        self.assertEqual(self.service.get("42", first.number).opener_id, "7")

    def test_allows_three_open_tickets_per_user_and_releases_slot_on_close(self):
        tickets = [
            self.service.create("42", "7", f"Support issue number {index} needs help.")
            for index in range(3)
        ]

        with self.assertRaisesRegex(SupportTicketError, "at most 3"):
            self.service.create("42", "7", "A fourth open support issue is blocked.")

        self.service.close("42", tickets[0].number, "99", "canceled")
        replacement = self.service.create("42", "7", "A replacement support issue is allowed.")
        self.assertEqual(replacement.number, "TICKET-000004")

    def test_claim_resolve_cancel_and_reopen_transitions_persist(self):
        ticket = self.service.create("42", "7", "The ticket transition needs verification.")
        assigned = self.service.claim("42", ticket.number, "99")
        resolved = self.service.close("42", ticket.number, "99", "resolved")
        reopened = self.service.reopen("42", ticket.number, "100")

        self.assertEqual(assigned.status, "assigned")
        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(reopened.status, "open")
        reloaded = SupportTicketService({}, self.root).get("42", ticket.number)
        self.assertEqual(reloaded.status, "open")
        self.assertEqual(
            [entry["action"] for entry in reloaded.history],
            ["opened", "assigned", "resolved", "reopened"],
        )

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

    def test_reopen_respects_three_active_ticket_limit(self):
        closed = self.service.create(
            "42", "7", "This ticket will be closed before the limit is filled."
        )
        self.service.close("42", closed.number, "99", "canceled")
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
