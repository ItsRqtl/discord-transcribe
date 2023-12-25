"""
The transcriber module of the bot.
"""

from io import BytesIO
from time import perf_counter
from typing import TYPE_CHECKING

import discord
from faster_whisper import WhisperModel

from src.utils.audio import Audio
from src.utils.embed import Embed

if TYPE_CHECKING:
    from src.main import Bot


class Transcriber:
    def __init__(self, client: "Bot", *args, **kwargs):
        self.client = client
        self.queue_size = None
        start = perf_counter()
        self.model = WhisperModel(*args, **kwargs)
        end = perf_counter()
        self.client.logger.debug(f"Loaded model in {end - start} seconds.")

    def transcribe_audiobytes(self, wav: BytesIO) -> str:
        """
        Transcribes an audio file read from a BytesIO object.

        :param audio: The audio file.
        :type audio: BytesIO

        :return: The transcribed text and the UUID of the transcription.
        :rtype: Tuple[str, UUID]
        """
        seg, _ = self.model.transcribe(wav, vad_filter=True)
        res = "".join([s.text.strip() for s in seg])
        return res

    async def process_queue(client: "Bot") -> None:
        """
        Process tasks from the queue.
        """
        while True:
            task = await client.database.get()
            client.transcriber.queue_size -= 1

            channel = await client.get_or_fetch_channel(task["channel_id"])
            if not channel:
                continue

            try:
                message = await channel.fetch_message(task["message_id"])
            except discord.NotFound:
                continue

            client.logger.info(f"Transcribing [{task['message_id']}] by [{task['user_id']}]")
            start = perf_counter()
            wav_file = await client.loop.run_in_executor(
                None, Audio.file_to_wav, await message.attachments[0].read()
            )
            transcribed = await client.loop.run_in_executor(
                None, client.transcriber.transcribe_audiobytes, wav_file
            )
            end = perf_counter()
            uid, time = await client.database.add_transcription(
                task["message_id"], task["channel_id"], transcribed
            )
            client.logger.info(
                f"Transcribed [Task {uid}] in {end - start} seconds. Output: {transcribed}"
            )

            await message.reply(
                f"<@{task['user_id']}>",
                embed=Embed.make_transcribed_embed(
                    message, transcribed, uid, time, task["locale"]
                ),
                mention_author=False,
            )
