import json
import typing

from . import abc
from .utils import Snowflake
from .enums import ChannelType
from typing import Optional, List, Union
from .route import Route

if typing.TYPE_CHECKING:
    from distee.message import Message


class BaseChannel(Snowflake):

    __slots__ = [
        'type'
    ]

    def __init__(self, **data):
        super(BaseChannel, self).__init__(**data)
        self.type: ChannelType = ChannelType(data.get('type'))


class GuildChannel(BaseChannel):

    __slots__ = [
        'guild_id',
        'name',
        'position',
        'nsfw',
        'permission_overwrites',
        'parent_id'
    ]
    
    def __init__(self, **data):
        super(GuildChannel, self).__init__(**data)
        self.guild_id: Optional[Snowflake] = Snowflake(id=data.get('guild_id')) \
            if data.get('guild_id') is not None else None
        self.name: str = data.get('name')
        self.position: int = data.get('position')
        self.nsfw: bool = data.get('nsfw')
        self.permission_overwrites: []  # FIXME parse permission overwrites
        self.parent_id: Optional[Snowflake] = Snowflake(id=data.get('parent_id')) \
            if data.get('parent_id') is not None else None


class Category(GuildChannel):
    
    def __init__(self, **data):
        super(Category, self).__init__(**data)


class MessageableChannel(BaseChannel, abc.Messageable):
    """Any channel that can contain text"""

    async def _get_channel(self) -> 'MessageableChannel':
        return self

    async def delete_message(self, msg_id: Union[Snowflake, int], reason: Optional[str] = None):
        await self._client.http.request(Route('DELETE',
                                              '/channels/{channel_id}/messages/{message_id}',
                                              guild_id=self.guild_id if isinstance(self, GuildChannel) else None,
                                              channel_id=self.id,
                                              message_id=msg_id),
                                        reason=reason)


class TextChannel(GuildChannel, MessageableChannel):
    """A Guild text channel"""

    __slots__ = [
        'rate_limit_per_user',
        'topic',
        'last_message_id',
        'default_auto_archive_duration'
    ]

    def __init__(self, **data):
        super(TextChannel, self).__init__(**data)
        self.rate_limit_per_user: int = data.get('rate_limit_per_user')
        self.topic: str = data.get('topic')
        self.last_message_id: Optional[Snowflake] = Snowflake(id=data.get('last_message_id')) \
            if data.get('last_message_id') is not None else None
        self.default_auto_archive_duration: int = data.get('default_auto_archive_duration')

    async def change_topic(self, new_topic: str):
        c_d = await self._client.http.request(Route('PATCH',
                                                    f'/channels/{self.id}',
                                                    channel_id=self.id,
                                                    guild_id=self.guild_id.id),
                                              json={'topic': new_topic})
        # TODO: handle errors
        self.topic = new_topic


class VoiceChannel(GuildChannel):

    __slots__ = [
        'bitrate',
        'user_limit',
        'rtc_region'
    ]

    def __init__(self, **data):
        super(VoiceChannel, self).__init__(**data)
        self.bitrate: int = data.get('bitrate')
        self.user_limit: int = data.get('user_limit')
        self.rtc_region: Optional[str] = data.get('rtc_region')


class DMChannel(MessageableChannel):
    
    def __init__(self, **data):
        super(DMChannel, self).__init__(**data)
    pass


def get_channel(**data):
    """Returns the correct channel class based on the ChannelType"""
    t = ChannelType(data.get('type'))
    if t == ChannelType.GUILD_TEXT:
        return TextChannel(**data)
    if t == ChannelType.GUILD_CATEGORY:
        return Category(**data)
    if t == ChannelType.GUILD_VOICE:
        return VoiceChannel(**data)
    if t == ChannelType.GUILD_STORE:
        return GuildChannel(**data)
    # FIXME: make this proper
    if t == ChannelType.FORUM_CHANNEL:
        return GuildChannel(**data)
    if t == ChannelType.GUILD_DIRECTORY:
        return GuildChannel(**data)
    if t == ChannelType.DM:
        return DMChannel(**data)

    return BaseChannel(**data)
