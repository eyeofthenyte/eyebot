import unittest

import discord

from cogs.bugreport import BugReportView, ReportModal, download_attachments
from services.bugReportService import ReportAttachment


class FakeService:
    settings = {
        "max_explanation_length": 4000,
        "max_attachments": 3,
        "max_attachment_bytes": 1024,
    }

    def __init__(self):
        self.validated_attachments = None

    def validate_attachments(self, attachments):
        self.validated_attachments = tuple(attachments)

    @staticmethod
    def safe_error(error):
        return f"{type(error).__name__}: {error}"


class FakeLogger:
    def __init__(self):
        self.info_messages = []
        self.error_messages = []

    def info(self, message, **metadata):
        self.info_messages.append((message, metadata))

    def error(self, message, **metadata):
        self.error_messages.append((message, metadata))


class FakeResponse:
    def __init__(self, *, modal_error=None):
        self.modal_error = modal_error
        self.modal = None
        self.message = None

    def is_done(self):
        return False

    async def send_modal(self, modal):
        if self.modal_error:
            raise self.modal_error
        self.modal = modal

    async def send_message(self, message, **kwargs):
        self.message = (message, kwargs)


class FakeFollowup:
    def __init__(self):
        self.message = None

    async def send(self, message, **kwargs):
        self.message = (message, kwargs)


class FakeInteraction:
    def __init__(self, *, modal_error=None):
        self.user = type("User", (), {"id": 42})()
        self.response = FakeResponse(modal_error=modal_error)
        self.followup = FakeFollowup()


class FakeAttachment:
    def __init__(self, filename="proof.png", content_type="image/png", data=b"png"):
        self.filename = filename
        self.content_type = content_type
        self.data = data
        self.size = len(data)
        self.read_count = 0

    async def read(self, *, use_cached=False):
        self.read_count += 1
        return self.data


def build_view():
    return BugReportView(
        service=FakeService(),
        logger=FakeLogger(),
        user_id=42,
        origin_name="Test Guild",
        guild_id="123",
        channel_name="general",
        channel_id="456",
        attachments=(),
    )


class BugReportInteractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_report_type_selection_opens_modal_immediately(self):
        view = build_view()
        selector = view.children[0]
        selector._values = ["bug"]
        interaction = FakeInteraction()

        await selector.callback(interaction)

        self.assertIsInstance(interaction.response.modal, ReportModal)
        self.assertEqual(interaction.response.modal.report_type, "bug")
        self.assertTrue(view.logger.info_messages)
        self.assertFalse(view.logger.error_messages)

    async def test_every_modal_placeholder_respects_discord_limit(self):
        view = build_view()

        for report_type in ("bug", "feature", "other"):
            with self.subTest(report_type=report_type):
                modal = ReportModal(view, report_type)
                for label in modal.children:
                    self.assertIsInstance(label, discord.ui.Label)
                    component = label.component
                    if isinstance(component, discord.ui.TextInput):
                        self.assertLessEqual(len(component.placeholder or ""), 100)

    async def test_modal_uses_labels_and_optional_bounded_file_upload(self):
        view = build_view()

        bug_modal = ReportModal(view, "bug")
        self.assertEqual(len(bug_modal.children), 5)
        self.assertIsInstance(bug_modal.attachments_input, discord.ui.FileUpload)
        self.assertFalse(bug_modal.attachments_input.required)
        self.assertEqual(bug_modal.attachments_input.min_values, 0)
        self.assertEqual(bug_modal.attachments_input.max_values, 3)

        feature_modal = ReportModal(view, "feature")
        self.assertEqual(len(feature_modal.children), 3)

    async def test_legacy_attachments_reduce_modal_upload_capacity(self):
        view = build_view()
        view.attachments = (
            ReportAttachment("legacy.png", "image/png", b"png"),
        )

        modal = ReportModal(view, "bug")

        self.assertEqual(modal.attachments_input.max_values, 2)

    async def test_ephemeral_modal_attachment_is_downloaded_immediately(self):
        service = FakeService()
        attachment = FakeAttachment()

        result = await download_attachments(service, [attachment])

        self.assertEqual(attachment.read_count, 1)
        self.assertEqual(result[0].filename, "proof.png")
        self.assertEqual(service.validated_attachments, result)

    async def test_report_type_failure_returns_response_and_is_logged(self):
        view = build_view()
        selector = view.children[0]
        selector._values = ["feature"]
        interaction = FakeInteraction(modal_error=RuntimeError("modal failed"))

        await selector.callback(interaction)

        self.assertIsNotNone(interaction.response.message)
        self.assertIn("could not open", interaction.response.message[0])
        self.assertTrue(view.logger.error_messages)


if __name__ == "__main__":
    unittest.main()
