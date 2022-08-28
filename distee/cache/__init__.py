from abc import ABC, abstractmethod
from typing import Optional, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from distee.guild import Guild, Member
    from distee.message import Message
    from distee.utils import Snowflake


class BaseMessageCache(ABC):

    @abstractmethod
    async def message_added(self, message: 'Message'):
        """Called when a message got added"""
        pass

    @abstractmethod
    async def message_deleted(self, msg_id: Union[int, Snowflake]) -> Optional['Message']:
        """Called when a message got deleted, returns the deleted message if still in cache"""
        pass

    @abstractmethod
    async def message_edited(self, message: 'Message') -> Optional['Message']:
        """Called when a message got edited, returns the pre edit message if in cache"""
        pass

    @abstractmethod
    async def get_message(self, msg_id: Union[int, Snowflake]) -> Optional['Message']:
        """Call this to get a message from the cache"""
        pass


class BaseGuildCache(ABC):

    @abstractmethod
    async def get_guild(self, guild_id: Union[int, 'Snowflake']) -> Optional['Guild']:
        """Call this to get a guild from the cache"""
        pass


class BaseMemberCache(ABC):

    @abstractmethod
    async def guild_left(self, guild_id: Union[int, 'Snowflake']):
        pass

    @abstractmethod
    async def member_added(self, member: 'Member'):
        pass

    @abstractmethod
    async def member_updated(self, member: 'Member') -> Optional['Member']:
        pass

    @abstractmethod
    async def member_removed(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        pass

    @abstractmethod
    async def get_member(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        pass
