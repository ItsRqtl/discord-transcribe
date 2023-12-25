"""
The main module of the bot.
"""

import logging
import tracemalloc
from typing import Union

import discord
from discord.ext import commands, tasks

from src.client.config import Config
from src.client.database import Database
from src.client.logging import InterceptHandler, Logging
from src.utils.transcriber import Transcriber


class Bot(discord.AutoShardedBot):
    """
    The modified discord bot client.
    """

    def __init__(self) -> None:
        self._client_ready = False
        self.current_presence = 0
        self.config = Config()
        self.logger = Logging(
            debug_mode=self.config["bot"]["debug-mode"],
            format=self.config["log"]["format"],
        ).get_logger()
        logging.basicConfig(
            handlers=[InterceptHandler(self.logger)],
            level=0 if self.config["bot"]["debug-mode"] else logging.INFO,
            force=True,
        )
        self.database = Database(self.config["database"]["path"])
        self.transcriber = Transcriber(self, **self.config["transcriber"])

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(owner_ids=self.config["bot"]["owners"], intents=intents)

        for k, v in self.load_extension("src.cogs", recursive=True, store=True).items():
            if v is True:
                self.logger.debug(f"Loaded extension {k}")
            else:
                self.logger.error(f"Failed to load extension {k} with exception: {v}")

    async def on_start(self) -> None:
        """
        The event that is triggered when the bot is started.
        """
        await self.database.initialize()
        self.transcriber.queue_size = await self.database.get_queue_size()
        self.loop.create_task(Transcriber.process_queue(self))
        self.update_presence.start()
        self.delete_outdated.start()
        self.logger.info(
            f"""
-------------------------
Logged in as: {self.user.name}#{self.user.discriminator} ({self.user.id})
Shards Count: {self.shard_count}
Memory Usage: {tracemalloc.get_traced_memory()[0] / 1024 ** 2:.2f} MB
 API Latency: {self.latency * 1000:.2f} ms
Guilds Count: {len(self.guilds)}
-------------------------"""
        )

    async def on_ready(self) -> None:
        """
        The event that is triggered when the bot is ready.
        """
        if self._client_ready:
            return
        await self.on_start()
        self._client_ready = True

    @tasks.loop(seconds=15)
    async def update_presence(self) -> None:
        """
        The loop that changes the bot's presence.
        """
        activities = [
            discord.Activity(type=discord.ActivityType.listening, name="voice notes."),
            discord.Game(f"{len(self.guilds)} servers."),
        ]
        self.current_presence += 1
        if self.current_presence >= len(activities):
            self.current_presence = 0
        await self.change_presence(activity=activities[self.current_presence])

    @tasks.loop(hours=3)
    async def delete_outdated(self) -> None:
        """
        The loop that removes outdated transcriptions.
        """
        await self.database.delete_outdated()

    def get_invite_url(self, permissions: Union[int, discord.Permissions]) -> str:
        """
        Gets the invite URL for the bot.

        :param permissions: The permissions to use.
        :type permissions: Union[int, discord.Permissions]

        :return: The invite URL.
        :rtype: str
        """
        if isinstance(permissions, int):
            permissions = discord.Permissions(permissions)
        return discord.utils.oauth_url(self.user.id, permissions=permissions)

    async def get_or_fetch_channel(
        self, id: int
    ) -> Union[discord.abc.GuildChannel, discord.Thread, discord.abc.PrivateChannel, None]:
        """
        Gets or fetches a channel.

        :param id: The ID of the channel.
        :type id: int

        :return: The channel.
        :rtype: GuildChannel | Thread | PrivateChannel | None
        """
        return await discord.utils.get_or_fetch(obj=self, attr="channel", id=id, default=None)


class BaseCog(commands.Cog):
    """
    The base cog class.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.client = bot
        self.config = bot.config
        self.logger = bot.logger
        self.database = bot.database
        self.transcriber = bot.transcriber
