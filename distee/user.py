from . import abc
from .channel import DMChannel, MessageableChannel
from .route import Route
from .utils import *
from typing import Optional
from .flags import UserFlags


class User(Snowflake, abc.Messageable):

    __slots__ = [
        'username',
        'discriminator',
        'avatar_hash',
        'flags',
        'public_flags',
        'dm_channel',
        'accent_color',
        'banner',
        'bot',
        'system'
    ]

    async def _get_channel(self) -> MessageableChannel:
        return await self.fetch_dm_channel()

    def __init__(self, **args):
        super(User, self).__init__(**args)
        self.dm_channel: Optional[DMChannel] = None
        self.username: str = args.get('username')
        self.discriminator: str = args.get('discriminator')
        self.avatar_hash: str = args.get("avatar")
        self.flags: UserFlags = UserFlags(args.get('flags') if args.get('flags') is not None else 0)
        self.public_flags: UserFlags = UserFlags(args.get('public_flags') if args.get('public_flags') is not None else 0)
        self.accent_color: Optional[int] = args.get('accent_color')
        self.banner: str = args.get('banner')
        self.bot: bool = args.get('bot', False)
        self.system: bool = args.get('system', False)

    @property
    def avatar(self) -> str:
        return f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_hash}.png'

    async def fetch_dm_channel(self):
        if self.dm_channel is not None:
            return self.dm_channel
        data = await self._client.http.request(Route('POST',
                                                     '/users/@me/channels'),
                                               json={'recipient_id': self.id})
        self.dm_channel = DMChannel(**data, _client=self._client)
        return self.dm_channel

