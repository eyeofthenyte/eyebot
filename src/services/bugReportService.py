"""Validation, redaction, and asynchronous SMTP delivery for bug reports."""

from __future__ import annotations

import asyncio
import html
import re
import secrets
import smtplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path


REPORT_TYPES = {
    "bug": ("Bug Report", "BUG"),
    "feature": ("Feature Request", "FEATURE"),
    "other": ("Other", "OTHER"),
}

EMAIL_PATTERN = re.compile(
    r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$",
    re.IGNORECASE,
)
SECRET_PATTERNS = (
    re.compile(
        r"(?i)\b(password|passwd|secret|token|api[_ -]?key|authorization)\b"
        r"\s*[:=]\s*([^\s,;]+)"
    ),
    re.compile(r"(?i)\b(bearer|oauth)\s*:?\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)([?&](?:access_token|token|key|secret)=)[^&#\s]+"),
    re.compile(r"\b(?:mfa\.)?[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}\b"),
)
SECRET_KEY_WORDS = ("password", "secret", "token", "credential", "api_key", "app_password")
ATTACHMENT_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}


class BugReportError(ValueError):
    """A user-safe report validation or delivery configuration error."""


@dataclass(frozen=True)
class ReportAttachment:
    filename: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class BugReport:
    report_id: str
    report_type: str
    submitted_at: datetime
    origin_name: str
    guild_id: str | None
    channel_name: str
    channel_id: str
    user_name: str
    user_id: str
    platform: str
    command: str
    explanation: str
    contact_email: str | None
    attachments: tuple[ReportAttachment, ...]


def validate_email(value: str | None) -> str | None:
    selected = str(value or "").strip()
    if not selected:
        return None
    if len(selected) > 254 or "\r" in selected or "\n" in selected:
        raise BugReportError("The contact email address is invalid.")
    local = selected.rsplit("@", 1)[0]
    if (
        not EMAIL_PATTERN.fullmatch(selected)
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
    ):
        raise BugReportError("The contact email address is invalid.")
    return selected


def _header(value: str, label: str) -> str:
    selected = str(value or "").strip()
    if not selected or "\r" in selected or "\n" in selected:
        raise BugReportError(f"The configured {label} is invalid.")
    return selected


class SecretRedactor:
    def __init__(self, config=None):
        self.known_values = tuple(sorted(self._known_secrets(config or {}), key=len, reverse=True))

    def _known_secrets(self, value, key="") -> set[str]:
        found = set()
        if isinstance(value, dict):
            for child_key, child in value.items():
                found.update(self._known_secrets(child, str(child_key).casefold()))
        elif isinstance(value, (list, tuple, set)):
            for child in value:
                found.update(self._known_secrets(child, key))
        elif any(word in key for word in SECRET_KEY_WORDS):
            selected = str(value or "")
            if len(selected) >= 6:
                found.add(selected)
        return found

    def redact(self, value: str) -> str:
        selected = str(value or "")
        for known in self.known_values:
            selected = selected.replace(known, "[REDACTED]")
        selected = SECRET_PATTERNS[0].sub(lambda match: f"{match.group(1)}=[REDACTED]", selected)
        selected = SECRET_PATTERNS[1].sub("[REDACTED AUTHORIZATION]", selected)
        selected = SECRET_PATTERNS[2].sub(lambda match: f"{match.group(1)}[REDACTED]", selected)
        selected = SECRET_PATTERNS[3].sub("[REDACTED TOKEN]", selected)
        return selected

    def contains_known_secret_bytes(self, data: bytes) -> bool:
        return any(known.encode("utf-8") in data for known in self.known_values)


class BugReportService:
    def __init__(self, config, logger=None, *, smtp_factory=None, smtp_ssl_factory=None):
        self.config = config
        self.settings = config.get("bug_reports", {})
        self.email_settings = config.get("email", {})
        self.logger = logger
        self.redactor = SecretRedactor(config)
        self.smtp_factory = smtp_factory or smtplib.SMTP
        self.smtp_ssl_factory = smtp_ssl_factory or smtplib.SMTP_SSL

    @property
    def enabled(self) -> bool:
        return self.settings.get("enabled") is True

    def new_report_id(self, report_type: str, now=None) -> str:
        if report_type not in REPORT_TYPES:
            raise BugReportError("The report type is invalid.")
        timestamp = now or datetime.now(timezone.utc)
        prefix = REPORT_TYPES[report_type][1]
        return f"{prefix}-{timestamp:%Y%m%d-%H%M%S}-{secrets.token_hex(3).upper()}"

    def build_report(
        self,
        *,
        report_type,
        origin_name,
        guild_id,
        channel_name,
        channel_id,
        user_name,
        user_id,
        explanation,
        platform="",
        command="",
        contact_email=None,
        attachments=(),
    ) -> BugReport:
        if report_type not in REPORT_TYPES:
            raise BugReportError("The report type is invalid.")
        maximum = min(4000, max(100, int(self.settings.get("max_explanation_length", 4000))))
        explanation = self.redactor.redact(str(explanation or "").strip())
        if not explanation:
            raise BugReportError("An explanation is required.")
        if len(explanation) > maximum:
            raise BugReportError(f"The explanation cannot exceed {maximum} characters.")

        platform = self.redactor.redact(str(platform or "").strip())[:100]
        command = self.redactor.redact(str(command or "").strip())[:200]
        if report_type == "bug" and (not platform or not command):
            raise BugReportError("Bug reports require both a platform and command.")
        selected_attachments = tuple(attachments)
        self.validate_attachments(selected_attachments)
        submitted_at = datetime.now(timezone.utc)
        return BugReport(
            report_id=self.new_report_id(report_type, submitted_at),
            report_type=report_type,
            submitted_at=submitted_at,
            origin_name=self.redactor.redact(str(origin_name or "Direct Message"))[:100],
            guild_id=str(guild_id) if guild_id else None,
            channel_name=self.redactor.redact(str(channel_name or "Direct Message"))[:100],
            channel_id=str(channel_id or ""),
            user_name=self.redactor.redact(str(user_name or "Unknown User"))[:100],
            user_id=str(user_id or ""),
            platform=platform,
            command=command,
            explanation=explanation,
            contact_email=validate_email(contact_email),
            attachments=selected_attachments,
        )

    def validate_attachments(self, attachments) -> None:
        maximum_count = max(0, min(10, int(self.settings.get("max_attachments", 3))))
        maximum_each = max(1, int(self.settings.get("max_attachment_bytes", 5_242_880)))
        maximum_total = max(maximum_each, int(self.settings.get("max_total_attachment_bytes", 10_485_760)))
        allowed = set(
            self.settings.get(
                "allowed_attachment_types",
                ("image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf", "text/plain"),
            )
        )
        if len(attachments) > maximum_count:
            raise BugReportError(f"A report may contain at most {maximum_count} attachments.")
        total = 0
        for attachment in attachments:
            if attachment.content_type not in allowed:
                raise BugReportError(f"Attachment `{attachment.filename}` uses an unsupported file type.")
            expected_type = ATTACHMENT_EXTENSIONS.get(
                Path(attachment.filename).suffix.casefold()
            )
            if expected_type != attachment.content_type:
                raise BugReportError(
                    f"Attachment `{attachment.filename}` has a mismatched file extension and content type."
                )
            if not self._matches_signature(attachment.content_type, attachment.data):
                raise BugReportError(
                    f"Attachment `{attachment.filename}` does not contain the declared file type."
                )
            if len(attachment.data) > maximum_each:
                raise BugReportError(f"Attachment `{attachment.filename}` exceeds the per-file size limit.")
            if self.redactor.contains_known_secret_bytes(attachment.data):
                raise BugReportError(f"Attachment `{attachment.filename}` contains a configured secret.")
            total += len(attachment.data)
        if total > maximum_total:
            raise BugReportError("The combined attachments exceed the report size limit.")

    @staticmethod
    def _matches_signature(content_type: str, data: bytes) -> bool:
        if content_type == "image/png":
            return data.startswith(b"\x89PNG\r\n\x1a\n")
        if content_type == "image/jpeg":
            return data.startswith(b"\xff\xd8\xff")
        if content_type == "image/gif":
            return data.startswith((b"GIF87a", b"GIF89a"))
        if content_type == "image/webp":
            return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
        if content_type == "application/pdf":
            return data.startswith(b"%PDF-")
        if content_type == "text/plain":
            return b"\x00" not in data[:4096]
        return False

    def sanitize_attachment(self, attachment: ReportAttachment) -> ReportAttachment:
        filename = Path(attachment.filename).name[:150] or "attachment"
        if attachment.content_type == "text/plain":
            text = attachment.data.decode("utf-8", errors="replace")
            data = self.redactor.redact(text).encode("utf-8")
        else:
            data = attachment.data
        return ReportAttachment(filename, attachment.content_type, data)

    def _plain_body(self, report: BugReport) -> str:
        label = REPORT_TYPES[report.report_type][0]
        rows = [
            f"Report ID: {report.report_id}",
            f"Type: {label}",
            f"Submitted UTC: {report.submitted_at.isoformat()}",
            "",
            f"Origin: {report.origin_name}",
            f"Guild ID: {report.guild_id or 'Direct Message'}",
            f"Channel: {report.channel_name} ({report.channel_id})",
            f"Discord user: {report.user_name} ({report.user_id})",
            f"Contact email: {report.contact_email or 'Not provided'}",
        ]
        if report.report_type == "bug":
            rows.extend((f"Platform: {report.platform}", f"Command: {report.command}"))
        rows.extend(("", "Explanation:", report.explanation))
        return "\n".join(rows)

    def _html_body(self, report: BugReport) -> str:
        return "<html><body><pre>" + html.escape(self._plain_body(report)) + "</pre></body></html>"

    def _message(self, report: BugReport) -> EmailMessage:
        recipient = _header(self.settings.get("recipient", ""), "bug-report recipient")
        sender = _header(self.settings.get("sender", ""), "bug-report sender")
        validate_email(recipient)
        validate_email(sender)
        subject_prefix = _header(self.settings.get("subject_prefix", "[EyeBot Report]"), "subject prefix")
        message = EmailMessage()
        message["To"] = recipient
        message["From"] = sender
        message["Subject"] = f"{subject_prefix} {report.report_id} {REPORT_TYPES[report.report_type][0]}"
        message.set_content(self._plain_body(report))
        message.add_alternative(self._html_body(report), subtype="html")
        for original in report.attachments:
            attachment = self.sanitize_attachment(original)
            main_type, sub_type = attachment.content_type.split("/", 1)
            message.add_attachment(
                attachment.data,
                maintype=main_type,
                subtype=sub_type,
                filename=attachment.filename,
            )
        return message

    def _send_sync(self, report: BugReport) -> None:
        host = _header(self.settings.get("smtp_host", ""), "SMTP host")
        port = int(self.settings.get("smtp_port", 587))
        timeout = max(1, min(120, int(self.settings.get("smtp_timeout", 15))))
        use_ssl = self.settings.get("smtp_ssl") is True
        use_starttls = self.settings.get("smtp_starttls", True) is True
        if use_ssl and use_starttls:
            raise BugReportError("SMTP SSL and STARTTLS cannot both be enabled.")
        username = str(self.email_settings.get("smtp_username") or "")
        password = str(self.email_settings.get("smtp_password") or "")
        factory = self.smtp_ssl_factory if use_ssl else self.smtp_factory
        smtp = factory(host, port, timeout=timeout)
        try:
            if use_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if username or password:
                if not username or not password:
                    raise BugReportError("Both SMTP username and password must be configured.")
                smtp.login(username, password)
            smtp.send_message(self._message(report))
        finally:
            try:
                smtp.quit()
            except (OSError, smtplib.SMTPException):
                smtp.close()

    async def send(self, report: BugReport) -> None:
        await asyncio.to_thread(self._send_sync, report)

    def safe_error(self, error: Exception) -> str:
        selected = self.redactor.redact(f"{type(error).__name__}: {error}")
        selected = re.sub(
            r"(?i)\b[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
            r"[A-Z0-9.-]+\.[A-Z]{2,}\b",
            "[REDACTED EMAIL]",
            selected,
        )
        return selected[:500]
