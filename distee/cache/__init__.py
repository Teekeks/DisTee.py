from abc import ABC, abstractmethod
from typing import Optional, Union

from distee.message import Message
from distee.utils import Snowflake


class BaseMessageCache(ABC):

    @abstractmethod
    async def message_added(self, message: Message):
        """Called when a message got added"""
        pass

    @abstractmethod
    async def message_deleted(self, msg_id: Union[int, Snowflake]) -> Optional[Message]:
        """Called when a message got deleted, returns the deleted message if still in cache"""
        pass

    @abstractmethod
    async def message_edited(self, message: Message) -> Optional[Message]:
        """Called when a message got edited, returns the pre edit message if in cache"""
        pass

    @abstractmethod
    async def get_message(self, msg_id: Union[int, Snowflake]) -> Optional[Message]:
        """Call this to get a message from the cache"""
        pass
