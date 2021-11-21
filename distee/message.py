import typing

from .utils import Snowflake
from typing import Optional, Union, List
from .http import Route
import json

if typing.TYPE_CHECKING:
    from .channel import TextChannel
    from .guild import Guild, Member
    from .user import User


class Message(Snowflake):

    def __init__(self, **args):
        super(Message, self).__init__(**args)
        self.content: str = args.get('content')
        self.guild_id: Snowflake = Snowflake(id=args.get('guild_id'))
        self.channel_id: Snowflake = Snowflake(id=args.get('channel_id'))
        self.author_id: Snowflake = Snowflake(id=args.get('author', {}).get('id'))
        self.pinned: bool = args.get('pinned')
        self.flags = args.get('flags')

        self.guild: Optional[Guild] = self._client.get_guild(self.guild_id) if self._client is not None else None
        self.channel: Optional[TextChannel] = self.guild.get_channel(self.channel_id) \
            if self.guild is not None else None
        self.author: Optional[Union[User, Member]] = self.guild.get_member(self.author_id) \
            if self.guild is not None else None
        if self.author is None and self._client is not None:
            self.author = self._client.get_user(self.author_id)
        self.embeds: Optional[List] = args.get('embeds')
        self.components: Optional[List] = args.get('components')
        # FIXME implement all of the message object https://discord.com/developers/docs/resources/channel#message-object

    @property
    def jump_url(self):
        return f'https://discord.com/channels/{self.guild_id.id}/{self.channel_id.id}/{self.id}'

    async def reply(self):
        pass

    def _get_reference(self, msg: 'Message') -> dict:
        return {
            'message_id': msg.id,
            'channel_id': msg.channel_id.id
        }

    async def edit(self,
                   content: str = None,
                   tts: bool = False,
                   reply_to: 'Message' = None,
                   embeds: Optional[List[dict]] = None,
                   components: Optional[List] = None,
                   allowed_mentions: Optional[dict] = None) -> 'Message':
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
        if allowed_mentions is not None:
            payload['allowed_mentions'] = allowed_mentions
        form.append({'name': 'payload_json', 'value': json.dumps(payload)})
        gid = self.guild_id.id if self.guild_id is not None else None
        data = await self._client.http.request(Route('PATCH',
                                                     f'/channels/{self.channel_id.id}/messages/{self.id}',
                                                     channel_id=self.channel_id.id,
                                                     guild_id=gid),
                                               form=form)
        return Message(**data, _client=self._client)

    async def delete(self, reason: Optional[str] = None):
        await self._client.http.request(Route('DELETE',
                                              '/channels/{channel_id}/messages/{message_id}',
                                              channel_id=self.channel_id,
                                              guild_id=self.guild_id,
                                              message_id=self.id),
                                        reason=reason)
