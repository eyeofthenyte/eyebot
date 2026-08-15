import asyncio
import unittest
from datetime import datetime, timezone

from services.bugReportService import (
    BugReportError,
    BugReportService,
    ReportAttachment,
    SecretRedactor,
    validate_email,
)
from core.platform_secret_schema import validate_secret_name


class FakeSMTP:
    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_values = None
        self.message = None
        self.closed = False

    def starttls(self, context):
        self.started_tls = True

    def login(self, username, password):
        self.login_values = (username, password)

    def send_message(self, message):
        self.message = message

    def quit(self):
        self.closed = True

    def close(self):
        self.closed = True


def config():
    return {
        "bug_reports": {
            "enabled": True,
            "recipient": "support@example.com",
            "sender": "eyebot@example.com",
            "subject_prefix": "[EyeBot Report]",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_starttls": True,
            "smtp_ssl": False,
            "smtp_timeout": 12,
            "max_explanation_length": 4000,
            "max_attachments": 3,
            "max_attachment_bytes": 1024,
            "max_total_attachment_bytes": 2048,
            "allowed_attachment_types": ["image/png", "text/plain"],
        },
        "email": {
            "smtp_username": "mailer",
            "smtp_password": "smtp-password-value",
        },
        "discord": {"bot_token": "known-discord-token"},
    }


class BugReportServiceTests(unittest.TestCase):
    def test_email_smtp_secrets_are_allowlisted(self):
        self.assertEqual(
            validate_secret_name("email", "smtp_password"),
            ("email", "smtp_password"),
        )

    def test_email_validation_rejects_invalid_and_header_injection(self):
        self.assertEqual(validate_email("person@example.com"), "person@example.com")
        self.assertIsNone(validate_email(""))
        for value in ("not-an-email", "a@example.com\nBcc:x@example.com"):
            with self.assertRaises(BugReportError):
                validate_email(value)

    def test_redacts_configured_and_pattern_secrets(self):
        redactor = SecretRedactor(config())
        output = redactor.redact(
            "token=abc123456789 known-discord-token Bearer abcdefghijklmnop"
        )
        self.assertNotIn("abc123456789", output)
        self.assertNotIn("known-discord-token", output)
        self.assertNotIn("abcdefghijklmnop", output)
        self.assertIn("REDACTED", output)

    def test_safe_error_redacts_email_and_secrets(self):
        service = BugReportService(config())
        output = service.safe_error(
            RuntimeError("support@example.com rejected known-discord-token")
        )
        self.assertNotIn("support@example.com", output)
        self.assertNotIn("known-discord-token", output)

    def test_bug_report_requires_platform_and_command(self):
        service = BugReportService(config())
        with self.assertRaisesRegex(BugReportError, "platform and command"):
            service.build_report(
                report_type="bug",
                origin_name="Guild",
                guild_id="42",
                channel_name="support",
                channel_id="5",
                user_name="tester",
                user_id="7",
                explanation="This is a detailed explanation.",
            )

    def test_report_redacts_fields_and_generates_trace_id(self):
        service = BugReportService(config())
        report = service.build_report(
            report_type="bug",
            origin_name="Guild",
            guild_id="42",
            channel_name="support",
            channel_id="5",
            user_name="tester",
            user_id="7",
            platform="Discord",
            command="!test token=abc123456789",
            explanation="The command used known-discord-token and then failed.",
            contact_email="person@example.com",
        )
        self.assertRegex(report.report_id, r"^BUG-\d{8}-\d{6}-[A-F0-9]{6}$")
        self.assertNotIn("known-discord-token", report.explanation)
        self.assertNotIn("abc123456789", report.command)

    def test_attachment_requires_matching_extension_mime_and_signature(self):
        service = BugReportService(config())
        valid = ReportAttachment("proof.png", "image/png", b"\x89PNG\r\n\x1a\nbody")
        service.validate_attachments((valid,))
        with self.assertRaisesRegex(BugReportError, "mismatched"):
            service.validate_attachments(
                (ReportAttachment("proof.txt", "image/png", valid.data),)
            )
        with self.assertRaisesRegex(BugReportError, "declared file type"):
            service.validate_attachments(
                (ReportAttachment("proof.png", "image/png", b"not a png"),)
            )

    def test_text_attachment_is_redacted_before_email(self):
        service = BugReportService(config())
        attachment = ReportAttachment(
            "details.txt",
            "text/plain",
            b"password=abc123456789",
        )
        sanitized = service.sanitize_attachment(attachment)
        self.assertNotIn(b"abc123456789", sanitized.data)

    def test_html_body_escapes_user_content(self):
        service = BugReportService(config())
        report = service.build_report(
            report_type="other",
            origin_name="Guild",
            guild_id="42",
            channel_name="support",
            channel_id="5",
            user_name="tester",
            user_id="7",
            explanation="A long enough <script>alert('x')</script> explanation.",
        )
        body = service._html_body(report)
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_async_smtp_delivery_uses_timeout_tls_and_login(self):
        created = []

        def factory(host, port, timeout):
            smtp = FakeSMTP(host, port, timeout)
            created.append(smtp)
            return smtp

        service = BugReportService(config(), smtp_factory=factory)
        report = service.build_report(
            report_type="feature",
            origin_name="Guild",
            guild_id="42",
            channel_name="support",
            channel_id="5",
            user_name="tester",
            user_id="7",
            explanation="Please add a useful new feature to EyeBot.",
        )
        asyncio.run(service.send(report))
        smtp = created[0]
        self.assertEqual(smtp.timeout, 12)
        self.assertTrue(smtp.started_tls)
        self.assertEqual(smtp.login_values, ("mailer", "smtp-password-value"))
        self.assertEqual(smtp.message["To"], "support@example.com")
        self.assertTrue(smtp.closed)

    def test_report_id_uses_utc_timestamp(self):
        service = BugReportService(config())
        selected = datetime(2026, 8, 15, 14, 30, 0, tzinfo=timezone.utc)
        self.assertRegex(
            service.new_report_id("other", selected),
            r"^OTHER-20260815-143000-[A-F0-9]{6}$",
        )


if __name__ == "__main__":
    unittest.main()
