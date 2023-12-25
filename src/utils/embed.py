"""
This file contains a modified version of discord.Embed
"""

from datetime import datetime, timezone

import discord

from src.client.i18n import I18n


class Embed(discord.Embed):
    """
    Modified version of discord.Embed, automatically sets the footer.
    """

    def escape_markdown(text: str) -> str:
        """
        Escapes markdown in a string.

        :param text: The text to escape.
        :type text: str

        :return: The escaped text.
        :rtype: str
        """
        return discord.utils.escape_markdown(text)

    @classmethod
    def make_error_embed(cls, identifier: str, locale, *args, **kwargs) -> discord.Embed:
        """
        Creates an embed for an error.

        :param identifier: The identifier of the error.
        :type identifier: str
        :param locale: The locale to use.
        :type locale: str | discord.ApplicationContext | discord.Interaction

        :return: The embed.
        :rtype: discord.Embed
        """
        return cls(
            title=I18n.get("embed.global.error.title", locale),
            description=I18n.get(f"embed.{identifier}", locale, *args, **kwargs),
            color=discord.Color.brand_red(),
        )

    @classmethod
    def make_queue_embed(cls, identifier: str, locale, *args, **kwargs) -> discord.Embed:
        """
        Creates an embed for the queue.

        :param identifier: The identifier of the queue.
        :type identifier: str
        :param locale: The locale to use.
        :type locale: str | discord.ApplicationContext | discord.Interaction

        :return: The embed.
        :rtype: discord.Embed
        """
        return cls(
            title=I18n.get("embed.transcribe.queue.title", locale),
            description=I18n.get(f"embed.transcribe.queue.{identifier}", locale, *args, **kwargs),
            color=discord.Color.blurple(),
        )

    @classmethod
    def make_transcribed_embed(
        cls, original: discord.Message, transcribed: str, uid: int, created_at: int, locale
    ) -> discord.Embed:
        """
        Creates an embed for a transcribed message.

        :param original: The original message.
        :type original: discord.Message
        :param transcribed: The transcribed text.
        :type transcribed: str
        :param uid: The ID of the transcription.
        :type uid: int
        :param created_at: The timestamp of the transcription.
        :type created_at: int
        :param locale: The locale to use.
        :type locale: str | discord.ApplicationContext | discord.Interaction

        :return: The embed.
        :rtype: discord.Embed
        """
        if not transcribed:
            description = I18n.get(
                "embed.transcribe.transcribed.no-transcription",
                locale,
                ori=original.jump_url,
                uid=uid,
            )
        else:
            description = (
                f"> {original.jump_url}```{cls.escape_markdown(transcribed)}```ID: `{uid}`"
            )

        return cls(
            title=I18n.get("embed.transcribe.transcribed.title", locale),
            description=description,
            color=discord.Color.brand_green(),
            timestamp=datetime.fromtimestamp(created_at, tz=timezone.utc),
        ).set_footer(text=I18n.get("embed.transcribe.transcribed.footer", locale))
