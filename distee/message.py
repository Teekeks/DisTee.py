from .utils import Snowflake
from .channel import TextChannel
from .guild import Guild, Member
from typing import Optional, Union, List
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
        # FIXME implement all of the message object https://discord.com/developers/docs/resources/channel#message-object

    @property
    def jump_url(self):
        return f'https://discord.com/channels/{self.guild_id.id}/{self.channel_id.id}/{self.id}'

    async def reply(self):
        pass
