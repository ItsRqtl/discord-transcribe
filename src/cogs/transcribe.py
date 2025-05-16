"""
Cog module for the transcribe commands.
"""

import discord
from discord.ext import commands

from src.client.i18n import message_command
from src.main import BaseCog, Bot
from src.utils.embed import Embed


class Transcribe(BaseCog):
    """
    The cog class for the transcribe commands.
    """

    def has_voice_note(self, message: discord.Message) -> bool:
        """
        Checks if a message has a voice note.

        :param message: The message to check.
        :type message: discord.Message

        :return: Whether the message has a voice note.
        :rtype: bool
        """
        return message.attachments and message.flags.value >> 13

    @BaseCog.listener()
    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, error: Exception
    ) -> None:
        """
        The error handler for the cog.
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                embed=Embed.make_error_embed(
                    "global.cooldown.description", ctx, cooldown=error.retry_after
                ),
                ephemeral=True,
            )
        else:
            raise error

    @message_command("transcribe")
    @discord.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def transcribe(self, ctx: discord.ApplicationContext, message: discord.Message) -> None:
        """
        Message command that transcribes a voice message.

        :param ctx: The context of the command.
        :type ctx: discord.ApplicationContext
        :param message: The message that the command was invoked with.
        :type message: discord.Message
        """
        await ctx.defer(ephemeral=True)
        if not self.has_voice_note(message):
            embed = Embed.make_error_embed("transcribe.no-voice-note", ctx)
            self.transcribe.reset_cooldown(ctx)
        elif not await self.client.is_owner(ctx.author) and await self.database.user_in_queue(
            ctx.author.id
        ):
            embed = Embed.make_error_embed("transcribe.user-in-queue", ctx)
            self.transcribe.reset_cooldown(ctx)
        elif await self.database.message_in_queue(message.id):
            embed = Embed.make_error_embed("transcribe.message-in-queue", ctx)
            self.transcribe.reset_cooldown(ctx)
        elif message.attachments[0].duration_secs > 60:
            embed = Embed.make_error_embed("transcribe.too-long", ctx)
            self.transcribe.reset_cooldown(ctx)
        elif data := await self.database.get_transcription(message.id, message.channel.id):
            embed = Embed.make_transcribed_embed(
                message, data["text"], data["id"], data["created_at"], ctx
            )
        else:
            if self.database.task_available.is_set():
                embed = Embed.make_queue_embed(
                    "added", ctx, position=self.transcriber.queue_size + 1
                )
            else:
                embed = Embed.make_queue_embed("starting", ctx)
            await self.database.add_to_queue(
                ctx.author.id,
                message.id,
                message.channel.id,
                ctx.locale or ctx.guild_locale or "en-US",
            )
            self.transcriber.queue_size += 1
        await ctx.respond(embed=embed)


def setup(bot: Bot) -> None:
    """
    The setup function of the cog.
    """
    bot.add_cog(Transcribe(bot))
