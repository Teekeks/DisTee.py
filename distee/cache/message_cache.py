from typing import Union, Optional

from distee.cache import BaseMessageCache
from distee.message import Message
from distee.utils import Snowflake


class NoMessageCache(BaseMessageCache):
    """Strategy: no message cache"""
    async def message_added(self, message: Message):
        pass

    async def message_deleted(self, msg_id: Union[int, Snowflake]) -> Optional[Message]:
        return None

    async def message_edited(self, message: Message) -> Optional[Message]:
        return None

    async def get_message(self, msg_id: Union[int, Snowflake]) -> Optional[Message]:
        return None


class GlobalRamMessageCache(BaseMessageCache):
    """Strategy: have a fixed size of messages cached in ram regardless of number of guilds.
    Throws out the oldest message by touch date"""

    def __init__(self, max_size: int = 10000):
        self.msg_cache = {}
        self.touch_date = {}
        self.counter = 0
        self.max_size: int = max_size

    def _handle_cache_length(self):
        while len(self.msg_cache.keys()) > self.max_size:
            # get message that was touched the longest time ago
            c = min(self.touch_date.keys())
            msg_id = self.touch_date.pop(c)
            self.msg_cache.pop(msg_id)

    def _get_touch_key(self, msg_id: int) -> Optional[int]:
        for key, mid in self.touch_date.items():
            if mid == msg_id:
                return key
        return None

    async def message_added(self, message: Message):
        self.msg_cache[message.id] = message
        self.touch_date[self.counter] = message.id
        self.counter += 1
        self._handle_cache_length()

    async def message_deleted(self, msg_id: Union[int, Snowflake]) -> Optional[Message]:
        msg_id = msg_id if isinstance(msg_id, int) else msg_id.id
        touch_key = self._get_touch_key(msg_id)
        if touch_key is not None:
            self.touch_date.pop(touch_key)
        msg = self.msg_cache.pop(msg_id, None)
        return msg

    async def message_edited(self, message: Message) -> Optional[Message]:
        touch_key = self._get_touch_key(message.id)
        if touch_key is not None:
            self.touch_date.pop(touch_key)
        msg = self.msg_cache.get(message.id, None)
        self.msg_cache[message.id] = message
        self.touch_date[self.counter] = message.id
        self.counter += 1
        return msg

    async def get_message(self, msg_id: Union[int, Snowflake]) -> Optional[Message]:
        return self.msg_cache.get(msg_id if isinstance(msg_id, int) else msg_id.id)
