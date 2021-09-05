from .utils import Snowflake
from .channel import TextChannel
from .guild import Guild, Member
from typing import Optional, Union
from .user import User


class Message(Snowflake):

    def __init__(self, **args):
        super(Message, self).__init__(**args)
        self.content = args.get('content')
        self.guild_id = Snowflake(id=args.get('guild_id'))
        self.channel_id = Snowflake(id=args.get('channel_id'))
        self.author_id = Snowflake(id=args.get('author', {}).get('id'))
        self.pinned = args.get('pinned')
        self.flags = args.get('flags')

        self.guild: Optional[Guild] = self._client.get_guild(self.guild_id) if self._client is not None else None
        self.channel: Optional[TextChannel] = self.guild.get_channel(self.channel_id) \
            if self.guild is not None else None
        self.author: Optional[Union[User, Member]] = self.guild.get_member(self.author_id) \
            if self.guild is not None else None
        if self.author is None and self._client is not None:
            self.author = self._client.get_user(self.author_id)

    async def reply(self):
        pass
