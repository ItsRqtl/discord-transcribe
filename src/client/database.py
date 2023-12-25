"""
The database module of the bot.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import aiosqlite


class Database:
    """
    The database class of the bot.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self.task_available = asyncio.Event()

    async def initialize(self) -> None:
        """
        Initializes the database.
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    locale TEXT NOT NULL
                );
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )
            await db.commit()

            async with db.execute("SELECT COUNT(*) FROM queue") as cursor:
                if (await cursor.fetchone())[0] > 0:
                    self.task_available.set()

    async def user_in_queue(self, user_id: int) -> bool:
        """
        Checks if a user is in the queue.

        :param user_id: The ID of the user.
        :type user_id: int

        :return: Whether the user is in the queue.
        :rtype: bool
        """
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM queue WHERE user_id = ?", (user_id,)
            ) as cursor:
                return bool((await cursor.fetchone())[0])

    async def message_in_queue(self, message_id: int) -> bool:
        """
        Checks if a message is in the queue.

        :param message_id: The ID of the message.
        :type message_id: int

        :return: Whether the message is in the queue.
        :rtype: bool
        """
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM queue WHERE message_id = ?", (message_id,)
            ) as cursor:
                return bool((await cursor.fetchone())[0])

    async def add_to_queue(
        self, user_id: int, message_id: int, channel_id: int, locale: str
    ) -> None:
        """
        Adds a message to the queue.

        :param user_id: The ID of the user that invoked the command.
        :type user_id: int
        :param message_id: The ID of the message.
        :type message_id: int
        :param channel_id: The ID of the channel.
        :type channel_id: int
        :param locale: The locale to use.
        :type locale: str
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO queue (user_id, message_id, channel_id, locale)
                VALUES (?, ?, ?, ?);
                """,
                (user_id, message_id, channel_id, locale),
            )
            await db.commit()
            self.task_available.set()

    async def get_queue_size(self) -> int:
        """
        Gets the size of the queue.

        :return: The size of the queue.
        :rtype: int
        """
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT COUNT(*) FROM queue") as cursor:
                return (await cursor.fetchone())[0]

    async def get(self) -> Optional[Dict[str, int]]:
        """
        Pops the first message from the queue.
        If queue is empty, wait until an item is available.

        :return: The popped message.
        :rtype: Optional[Dict[str, int]]
        # {"id": int, "user_id": int, "message_id": int, "channel_id": int, "locale": str}
        """
        while True:
            async with aiosqlite.connect(self.path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM queue ORDER BY id ASC LIMIT 1") as cursor:
                    message = await cursor.fetchone()
                if message:
                    await db.execute("DELETE FROM queue WHERE id = ?", (message["id"],))
                    await db.commit()
                    return dict(message)
                else:
                    await self.task_available.wait()
                    self.task_available.clear()

    async def add_transcription(
        self, message_id: int, channel_id: int, text: str
    ) -> Tuple[int, int]:
        """
        Adds a transcription to the database.

        :param message_id: The ID of the message.
        :type message_id: int
        :param channel_id: The ID of the channel.
        :type channel_id: int
        :param text: The transcribed text.
        :type text: str

        :return: The ID of the transcription and the timestamp.
        :rtype: Tuple[int, int]
        """
        async with aiosqlite.connect(self.path) as db:
            timestamp = int(datetime.now(timezone.utc).timestamp())
            async with db.execute(
                """
                INSERT INTO transcriptions (message_id, channel_id, text, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (message_id, channel_id, text, timestamp),
            ) as cursor:
                await db.commit()
                return cursor.lastrowid, timestamp

    async def get_transcription(
        self, message_id: int, channel_id: int
    ) -> Optional[Dict[str, int]]:
        """
        Gets a transcription from the database.

        :param message_id: The ID of the message.
        :type message_id: int
        :param channel_id: The ID of the channel.
        :type channel_id: int

        :return: The transcription.
        :rtype: Optional[Dict[str, int]]
        """
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM transcriptions WHERE message_id = ? AND channel_id = ?",
                (message_id, channel_id),
            ) as cursor:
                data = await cursor.fetchone()
                return dict(data) if data else None

    async def delete_outdated(self, days: int = 7) -> None:
        """
        Deletes outdated transcriptions.

        :param days: The number of days after which a transcription is considered outdated.
        :type days: int
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "DELETE FROM transcriptions WHERE created_at < ?",
                (int(datetime.now(timezone.utc).timestamp()) - days * 86400,),
            )
            await db.commit()
