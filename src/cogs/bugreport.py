"""Discord-only interactive bug and feature report workflow."""

from __future__ import annotations

import asyncio
import mimetypes

import discord
from discord.ext import commands

from services.bugReportService import (
    BugReportError,
    BugReportService,
    REPORT_TYPES,
    ReportAttachment,
)


GENERIC_FAILURE = (
    "❌ EyeBot could not submit that report. Please verify the form and try "
    "again later, or contact an EyeBot administrator."
)


async def download_attachments(
    service: BugReportService, source
) -> tuple[ReportAttachment, ...]:
    """Immediately download and validate Discord attachments.

    Modal uploads are ephemeral, so no Discord URL is retained for later use.
    """
    configured_count = max(
        0, min(10, int(service.settings.get("max_attachments", 3)))
    )
    if len(source) > configured_count:
        raise BugReportError(
            f"A report may contain at most {configured_count} attachments."
        )
    maximum_each = max(
        1, int(service.settings.get("max_attachment_bytes", 5_242_880))
    )
    results = []
    for attachment in source:
        if attachment.size > maximum_each:
            raise BugReportError(
                f"Attachment `{attachment.filename}` exceeds the per-file size limit."
            )
        content_type = str(
            attachment.content_type
            or mimetypes.guess_type(attachment.filename)[0]
            or "application/octet-stream"
        ).split(";", 1)[0].casefold()
        results.append(
            ReportAttachment(
                filename=attachment.filename,
                content_type=content_type,
                data=await attachment.read(use_cached=True),
            )
        )
    selected = tuple(results)
    service.validate_attachments(selected)
    return selected


class ReportModal(discord.ui.Modal):
    def __init__(self, view: "BugReportView", report_type: str):
        super().__init__(title=REPORT_TYPES[report_type][0], timeout=900)
        self.report_view = view
        self.report_type = report_type
        self.platform_input = None
        self.command_input = None
        if report_type == "bug":
            self.platform_input = discord.ui.TextInput(
                placeholder="Discord, Twitch, Kick, Instagram, etc.",
                required=True,
                max_length=100,
            )
            self.command_input = discord.ui.TextInput(
                placeholder="Example: !roll 1d20 or !platform twitch enable",
                required=True,
                max_length=200,
            )
            self.add_item(
                discord.ui.Label(text="Platform", component=self.platform_input)
            )
            self.add_item(
                discord.ui.Label(
                    text="Command being used", component=self.command_input
                )
            )
        self.explanation_input = discord.ui.TextInput(
            placeholder=(
                "Describe what happened, what you expected, and how to reproduce it. "
                "Do not include secrets."
            ),
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=10,
            max_length=view.maximum_explanation_length,
        )
        self.email_input = discord.ui.TextInput(
            placeholder="name@example.com",
            required=False,
            max_length=254,
        )
        self.add_item(
            discord.ui.Label(text="Explanation", component=self.explanation_input)
        )
        self.add_item(
            discord.ui.Label(
                text="Contact email (optional)", component=self.email_input
            )
        )
        self.attachments_input = None
        remaining_attachments = max(
            0,
            self.report_view.maximum_attachments
            - len(self.report_view.attachments),
        )
        if remaining_attachments:
            self.attachments_input = discord.ui.FileUpload(
                required=False,
                min_values=0,
                max_values=remaining_attachments,
            )
            self.add_item(
                discord.ui.Label(
                    text="Attachments (optional)",
                    description=(
                        "Upload screenshots, logs, PDFs, or text files. Remove "
                        "visible passwords and tokens first."
                    ),
                    component=self.attachments_input,
                )
            )

    async def on_submit(self, interaction: discord.Interaction):
        if not await self.report_view.claim_submission():
            return await interaction.response.send_message(
                "ℹ️ This report form has already been submitted.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True, thinking=True)
        service = self.report_view.service
        report = None
        try:
            modal_attachments = await download_attachments(
                service,
                self.attachments_input.values if self.attachments_input else (),
            )
            attachments = self.report_view.attachments + modal_attachments
            report = service.build_report(
                report_type=self.report_type,
                origin_name=self.report_view.origin_name,
                guild_id=self.report_view.guild_id,
                channel_name=self.report_view.channel_name,
                channel_id=self.report_view.channel_id,
                user_name=str(interaction.user),
                user_id=str(interaction.user.id),
                platform=(self.platform_input.value if self.platform_input else ""),
                command=(self.command_input.value if self.command_input else ""),
                explanation=self.explanation_input.value,
                contact_email=self.email_input.value,
                attachments=attachments,
            )
            await service.send(report)
        except BugReportError as error:
            self.report_view.submitted = False
            return await interaction.followup.send(f"❌ {error}", ephemeral=True)
        except Exception as error:
            logger = self.report_view.logger
            logger.error(
                f"Bug report delivery failed for "
                f"{report.report_id if report else 'unassigned report'}: "
                + service.safe_error(error),
                guild_id=self.report_view.guild_id,
            )
            return await interaction.followup.send(GENERIC_FAILURE, ephemeral=True)

        self.report_view.logger.info(
            f"Report {report.report_id} ({REPORT_TYPES[self.report_type][0]}) "
            f"submitted by Discord user ID {interaction.user.id}",
            guild_id=self.report_view.guild_id,
        )
        embed = discord.Embed(
            title="✅ Report Submitted",
            description="Your report was securely sent to the EyeBot support address.",
            color=0x2ECC71,
        )
        embed.add_field(name="Report ID", value=f"`{report.report_id}`", inline=False)
        embed.add_field(name="Type", value=REPORT_TYPES[self.report_type][0], inline=True)
        embed.add_field(
            name="Contact email",
            value="Provided" if report.contact_email else "Not provided",
            inline=True,
        )
        embed.set_footer(text="Keep the report ID for follow-up.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_error(self, interaction, error):
        self.report_view.logger.error(
            "Bug report modal failed: " + self.report_view.service.safe_error(error),
            guild_id=self.report_view.guild_id,
        )
        if interaction.response.is_done():
            await interaction.followup.send(GENERIC_FAILURE, ephemeral=True)
        else:
            await interaction.response.send_message(GENERIC_FAILURE, ephemeral=True)


class ReportTypeSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            custom_id="eyebot:bugreport:type",
            placeholder="Select the type of report…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Bug Report",
                    value="bug",
                    emoji="🐛",
                    description="Something is broken or behaving incorrectly.",
                ),
                discord.SelectOption(
                    label="Feature Request",
                    value="feature",
                    emoji="✨",
                    description="Suggest a new feature or improvement.",
                ),
                discord.SelectOption(
                    label="Other",
                    value="other",
                    emoji="📝",
                    description="Submit another kind of EyeBot report.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        view: BugReportView = self.view
        if view.submitted:
            return await interaction.response.send_message(
                "ℹ️ This report form has already been submitted.", ephemeral=True
            )
        report_type = self.values[0]
        view.logger.info(
            f"Discord user ID {interaction.user.id} selected bug report type "
            f"{report_type}",
            guild_id=view.guild_id,
        )
        try:
            modal = ReportModal(view, report_type)
            await interaction.response.send_modal(modal)
        except Exception as error:
            view.logger.error(
                "Bug report type selection failed: "
                + view.service.safe_error(error),
                guild_id=view.guild_id,
            )
            message = (
                "❌ EyeBot could not open the report form. Please run "
                "`!bugreport` again or contact an EyeBot administrator."
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(message, ephemeral=True)
                else:
                    await interaction.response.send_message(message, ephemeral=True)
            except Exception as response_error:
                view.logger.error(
                    "Bug report selection error response failed: "
                    + view.service.safe_error(response_error),
                    guild_id=view.guild_id,
                )


class BugReportView(discord.ui.View):
    def __init__(
        self,
        *,
        service,
        logger,
        user_id,
        origin_name,
        guild_id,
        channel_name,
        channel_id,
        attachments,
    ):
        super().__init__(timeout=900)
        self.service = service
        self.logger = logger
        self.user_id = int(user_id)
        self.origin_name = origin_name
        self.guild_id = str(guild_id) if guild_id else None
        self.channel_name = channel_name
        self.channel_id = str(channel_id)
        self.attachments = tuple(attachments)
        self.maximum_attachments = max(
            0, min(10, int(service.settings.get("max_attachments", 3)))
        )
        self.maximum_explanation_length = min(
            4000,
            max(100, int(service.settings.get("max_explanation_length", 4000))),
        )
        self.submitted = False
        self._submission_lock = asyncio.Lock()
        self.add_item(ReportTypeSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.user_id:
            return True
        await interaction.response.send_message(
            "❌ Only the person who opened this report may use the form.",
            ephemeral=True,
        )
        return False

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        item_name = type(item).__name__
        self.logger.error(
            f"Bug report view item {item_name} failed: "
            + self.service.safe_error(error),
            guild_id=self.guild_id,
        )
        message = (
            "❌ EyeBot could not process that report selection. Please run "
            "`!bugreport` again or contact an EyeBot administrator."
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception as response_error:
            self.logger.error(
                "Bug report view error response failed: "
                + self.service.safe_error(response_error),
                guild_id=self.guild_id,
            )

    async def claim_submission(self) -> bool:
        async with self._submission_lock:
            if self.submitted:
                return False
            self.submitted = True
            return True


class BugReportCog(commands.Cog, name="Bug Reports"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.service = BugReportService(bot.config, bot.logger)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        data = interaction.data if isinstance(interaction.data, dict) else {}
        if data.get("custom_id") != "eyebot:bugreport:type":
            return
        guild_id = str(interaction.guild_id) if interaction.guild_id else None
        self.logger.info(
            f"Received bug report type interaction from Discord user ID "
            f"{interaction.user.id}",
            guild_id=guild_id,
        )

    @commands.command(
        name="bugreport",
        extras=[
            "🐛  **__Bug Report__**",
            "**Usage:** `!bugreport`\n"
            "EyeBot sends a private DM containing a report-type selector and "
            "structured form. Upload up to the configured limit of PNG, JPEG, "
            "GIF, WebP, PDF, or text files while completing the form. Files on "
            "the original command remain supported temporarily. "
            "Never include passwords, tokens, or other credentials.",
        ],
    )
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def bugreport(self, ctx):
        if not self.service.enabled:
            return await ctx.send("❌ Bug reporting is not currently available.")
        try:
            attachments = await download_attachments(
                self.service, ctx.message.attachments
            )
            guild = ctx.guild
            origin_name = guild.name if guild else "Direct Message"
            channel_name = getattr(ctx.channel, "name", None) or "Direct Message"
            embed = discord.Embed(
                title="EyeBot Report Form",
                description=(
                    "Select a report type below. EyeBot will then open a private "
                    "form tailored to your selection."
                ),
                color=0x5865F2,
            )
            embed.add_field(name="Started from", value=origin_name[:1024], inline=False)
            embed.add_field(
                name="Report types",
                value=(
                    "🐛 **Bug Report** — asks for platform, command, and explanation\n"
                    "✨ **Feature Request** — asks for the requested improvement\n"
                    "📝 **Other** — asks for a general explanation"
                ),
                inline=False,
            )
            embed.add_field(
                name="Contact email",
                value="Optional. Discord does not provide your account email to EyeBot.",
                inline=False,
            )
            embed.add_field(
                name="Attachments",
                value=(
                    f"{len(attachments)} attachment(s) captured from the command; "
                    "you may add more in the form up to the configured total. "
                    "Remove passwords, tokens, private keys, and visible credentials "
                    "from screenshots before submitting."
                ),
                inline=False,
            )
            embed.set_footer(text="This form expires after 15 minutes.")
            view = BugReportView(
                service=self.service,
                logger=self.logger,
                user_id=ctx.author.id,
                origin_name=origin_name,
                guild_id=guild.id if guild else None,
                channel_name=channel_name,
                channel_id=ctx.channel.id,
                attachments=attachments,
            )
            await ctx.author.send(embed=embed, view=view)
        except BugReportError as error:
            return await ctx.send(f"❌ {error}")
        except discord.Forbidden:
            return await ctx.send(
                "❌ I could not send you a DM. Enable direct messages from this "
                "server and run `!bugreport` again."
            )
        except Exception as error:
            self.logger.error(
                "Bug report form initialization failed: "
                + self.service.safe_error(error),
                guild_id=ctx.guild.id if ctx.guild else None,
            )
            return await ctx.send(GENERIC_FAILURE)

        self.logger.info(
            f"Discord user ID {ctx.author.id} opened a bug report form",
            guild_id=ctx.guild.id if ctx.guild else None,
        )
        if ctx.guild:
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
            await ctx.send(
                "📨 Check your DMs to complete the EyeBot report form.",
                delete_after=10,
            )


async def setup(bot):
    await bot.add_cog(BugReportCog(bot))
