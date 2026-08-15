import unittest

from cogs.bugreport import BugReportView, ReportModal


class FakeService:
    settings = {"max_explanation_length": 4000}

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
                for component in modal.to_components():
                    text_input = component["components"][0]
                    placeholder = text_input.get("placeholder", "")
                    self.assertLessEqual(len(placeholder), 100)

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
