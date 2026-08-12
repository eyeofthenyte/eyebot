import unittest

from adapters.kick_adapter import request_from_kick_chat_event
from core.command_model import CommandParseError, CommandPlatform, CommandSurface


def chat_payload(content="!r 1d20"):
    return {
        "message_id": "message-123",
        "broadcaster": {
            "user_id": 100,
            "username": "EyeBot Channel",
            "channel_slug": "eyebot_channel",
        },
        "sender": {
            "is_anonymous": False,
            "user_id": 200,
            "username": "DiceUser",
            "channel_slug": "diceuser",
            "is_verified": True,
            "profile_picture": "https://example.test/avatar.jpg",
            "identity": {
                "badges": [
                    {"text": "Moderator", "type": "moderator"},
                    {"text": "Subscriber", "type": "subscriber"},
                ]
            },
        },
        "content": content,
        "created_at": "2026-08-12T12:34:56Z",
    }


class KickCommandConverterTests(unittest.TestCase):
    def test_converts_roll_alias_and_preserves_kick_context(self):
        request = request_from_kick_chat_event(
            chat_payload(),
            prefix="!",
            headers={
                "Kick-Event-Type": "chat.message.sent",
                "Kick-Event-Version": "1",
                "Kick-Event-Subscription-Id": "subscription-456",
            },
        )

        self.assertEqual(request.platform, CommandPlatform.KICK)
        self.assertEqual(request.surface, CommandSurface.LIVESTREAM_CHAT)
        self.assertEqual(request.command, "r")
        self.assertEqual(request.arguments, ("1d20",))
        self.assertEqual(request.actor.id, "200")
        self.assertEqual(request.actor.username, "DiceUser")
        self.assertEqual(request.actor.roles, ("moderator", "subscriber"))
        self.assertEqual(request.location.channel_id, "100")
        self.assertEqual(request.location.channel_name, "eyebot_channel")
        self.assertEqual(request.metadata["message_id"], "message-123")
        self.assertEqual(request.metadata["subscription_id"], "subscription-456")

    def test_marks_the_channel_owner_as_broadcaster(self):
        payload = chat_payload("!oracle Will this work?")
        payload["sender"] = {
            **payload["sender"],
            "user_id": 100,
            "identity": {"badges": []},
        }

        request = request_from_kick_chat_event(payload, prefix="!")

        self.assertEqual(request.actor.roles, ("broadcaster",))
        self.assertEqual(request.command, "oracle")
        self.assertEqual(request.argument_text, "Will this work?")

    def test_rejects_non_command_text(self):
        with self.assertRaises(CommandParseError):
            request_from_kick_chat_event(chat_payload("hello"), prefix="!")

    def test_rejects_anonymous_sender(self):
        payload = chat_payload()
        payload["sender"]["is_anonymous"] = True

        with self.assertRaisesRegex(CommandParseError, "Anonymous"):
            request_from_kick_chat_event(payload, prefix="!")

    def test_rejects_non_chat_event(self):
        with self.assertRaisesRegex(CommandParseError, "not a chat"):
            request_from_kick_chat_event(
                chat_payload(),
                prefix="!",
                headers={"Kick-Event-Type": "livestream.status.updated"},
            )

    def test_rejects_missing_required_sender_data(self):
        payload = chat_payload()
        payload["sender"] = None

        with self.assertRaisesRegex(CommandParseError, "sender"):
            request_from_kick_chat_event(payload, prefix="!")


if __name__ == "__main__":
    unittest.main()
