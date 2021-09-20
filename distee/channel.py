import json

from .utils import Snowflake
from .enums import ChannelType
from typing import Optional, List
from .http import Route


class BaseChannel(Snowflake):

    def __init__(self, **data):
        super(BaseChannel, self).__init__(**data)
        self.type: ChannelType = ChannelType(data.get('type'))


class GuildChannel(BaseChannel):
    
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


class MessageableChannel(BaseChannel):

    def _get_reference(self, msg: 'Message') -> dict:
        return {
            'message_id': msg.id,
            'channel_id': msg.channel_id.id
        }

    async def send(self,
                   content: str = None,
                   tts: bool = False,
                   reply_to: 'Message' = None,
                   embeds: Optional[List[dict]] = None,
                   components: Optional[List] = None) -> 'Message':
        payload = {'tts': tts}
        form = []
        if content is not None:
            payload['content'] = content
        if reply_to is not None:
            payload['message_reference'] = self._get_reference(reply_to)
        if embeds is not None:
            payload['embeds'] = embeds
        if components is not None:
            payload['components'] = components
        form.append({'name': 'payload_json', 'value': json.dumps(payload)})
        await self._client.http.request(Route('POST', f'/channels/{self.id}/messages'), form=form)


class TextChannel(GuildChannel, MessageableChannel):

    def __init__(self, **data):
        super(TextChannel, self).__init__(**data)
        self.rate_limit_per_user: int = data.get('rate_limit_per_user')
        self.topic: str = data.get('topic')
        self.last_message_id: Optional[Snowflake] = Snowflake(id=data.get('last_message_id')) \
            if data.get('last_message_id') is not None else None
        self.default_auto_archive_duration: int = data.get('default_auto_archive_duration')

    async def change_topic(self, new_topic: str):
        c_d = await self._client.http.request(Route('PATCH', f'/channels/{self.id}'), json={'topic': new_topic})
        # TODO: handle errors
        self.topic = new_topic


class VoiceChannel(GuildChannel):

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
    if t == ChannelType.DM:
        return DMChannel(**data)

    return BaseChannel(**data)
