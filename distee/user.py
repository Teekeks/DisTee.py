from .utils import *
from typing import Optional
from .flags import UserFlags


class User(Snowflake):

    username: str = None
    discriminator: str = None
    avatar_hash: Optional[str] = None
    flags: UserFlags = 0
    public_flags: UserFlags

    def __init__(self, **args):
        super(User, self).__init__(**args)
        self.username = args.get('username')
        self.discriminator = args.get('discriminator')
        self.avatar_hash = args.get('avatar')
        self.avatar: str = f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_hash}.png'
        self.flags: UserFlags = UserFlags(args.get('flags') if args.get('flags') is not None else 0)
        self.public_flags: UserFlags = UserFlags(args.get('public_flags') if args.get('public_flags') is not None else 0)
        self.accent_color = args.get('accent_color')
        self.banner = args.get('banner')
        self.banner_color = args.get('banner_color')
        self.bot: bool = args.get('bot', False)
        self.system: bool = args.get('system', False)
