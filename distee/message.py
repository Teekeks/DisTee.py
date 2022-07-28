import typing

from .enums import MessageType
from .utils import Snowflake
from typing import Optional, Union, List
from .route import Route

if typing.TYPE_CHECKING:
    from .channel import TextChannel
    from .guild import Guild, Member
    from .user import User


class Message(Snowflake):

    __slots__ = [
        'content',
        'guild_id',
        'channel_id',
        'author_id',
        'pinned',
        'flags',
        'guild',
        'channel',
        'author',
        'embeds',
        'components',
        'type'
    ]

    def __init__(self, **args):
        super(Message, self).__init__(**args)
        self.content: str = args.get('content')
        self.guild_id: Snowflake = Snowflake(id=args.get('guild_id'))
        self.channel_id: Snowflake = Snowflake(id=args.get('channel_id'))
        self.author_id: Snowflake = Snowflake(id=args.get('author', {}).get('id'))
        self.pinned: bool = args.get('pinned')
        self.flags = args.get('flags')

        self.guild: Optional[Guild] = self._client.get_guild(self.guild_id) if self._client is not None else None
        self.author: Optional[Union[User, Member]] = self.guild.get_member(self.author_id) \
            if self.guild is not None else None
        if self.author is None and self._client is not None:
            self.author = self._client.get_user(self.author_id)
        self.channel: Optional[TextChannel] = self.guild.get_channel(self.channel_id) \
            if self.guild is not None else None
        self.embeds: Optional[List] = args.get('embeds')
        self.components: Optional[List] = args.get('components')
        self.type: MessageType = MessageType(args.get('type', 0))
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
        return await self._client.http.edit_message(Route('PATCH',
                                                          f'/channels/{self.channel_id.id}/messages/{self.id}',
                                                          channel_id=self.channel_id.id),
                                                    content=content,
                                                    tts=tts,
                                                    message_reference=self._get_reference(reply_to) if reply_to is not None else None,
                                                    embeds=embeds,
                                                    components=components,
                                                    allowed_mentions=allowed_mentions)

    async def delete(self, reason: Optional[str] = None):
        await self._client.http.request(Route('DELETE',
                                              '/channels/{channel_id}/messages/{message_id}',
                                              channel_id=self.channel_id,
                                              guild_id=self.guild_id,
                                              message_id=self.id),
                                        reason=reason)
