import typing

from .enums import MessageType
from .utils import Snowflake
from typing import Optional, Union, List
from .route import Route
import urllib.parse

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
        'author_is_webhook',
        'pinned',
        'flags',
        'guild',
        'channel',
        'embeds',
        'components',
        'type',
        'tts',
        'mention_everyone',
        'nonce',
        'webhook_id'
    ]

    def __init__(self, **args):
        super(Message, self).__init__(**args)
        self.content: str = args.get('content')
        self.guild_id: Snowflake = Snowflake(id=args.get('guild_id'))
        self.channel_id: Snowflake = Snowflake(id=args.get('channel_id'))
        self.author_id: Snowflake = Snowflake(id=args.get('author', {}).get('id'))
        self.author_is_webhook: bool = args.get('author', {}).get('discriminator', '') == '0000'
        self.pinned: bool = args.get('pinned')
        # TODO: fix flags to use message flags
        self.flags = args.get('flags')
        self.guild: Optional[Guild] = self._client.get_guild(self.guild_id) if self._client is not None else None
        self.channel: Optional[TextChannel] = self.guild.get_channel(self.channel_id) \
            if self.guild is not None else None
        self.embeds: Optional[List] = args.get('embeds')
        self.components: Optional[List] = args.get('components')
        self.type: MessageType = MessageType(args.get('type', 0))
        # TODO implement timestamp
        # TODO implement edited_timestamp
        self.tts: bool = args.get('tts')
        self.mention_everyone: bool = args.get('mention_everyone')
        # TODO implement mentions
        # TODO implement mention_roles
        # TODO implement mention_channels
        # TODO implement attachments
        # TODO implement reactions
        self.nonce: Optional[Union[int, str]] = args.get('nonce')
        self.webhook_id: Optional[Snowflake] = Snowflake(id=args.get('webhook_id')) if args.get('webhook_id') is not None else None
        # TODO implement activity
        # TODO implement application
        # TODO implement application_id
        # TODO implement message_reference
        # TODO implement referenced_message
        # TODO implement interaction
        # TODO implement thread
        # TODO implement sticker_items
        # TODO implement stickers
        # TODO implement position
        # FIXME implement all of the message object https://discord.com/developers/docs/resources/channel#message-object

    async def add_reaction(self, emoji):
        if isinstance(emoji, dict):
            emoji = f'{emoji["name"]}:{emoji["id"]}'
        emoji = urllib.parse.quote_plus(emoji)
        await self._client.http.request(Route('PUT', '/channels/{channel_id}/messages/{message_id}/reactions/{reaction}/@me',
                                              channel_id=self.channel_id,
                                              message_id=self.id,
                                              reaction=emoji))

    async def author(self):
        return await self.guild.obtain_member(self.author_id) if self.guild is not None else self._client.get_user(self.author_id)

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
