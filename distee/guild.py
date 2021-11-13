from .http import Route
from .utils import Snowflake
from typing import Optional, List, Dict, Union
from .enums import GuildVerificationLevel, MessageNotificationLevel, ExplicitContentFilterLevel, MFALevel, PremiumTier
from .enums import GuildNSFWLevel
from .flags import SystemChannelFlags
from .channel import GuildChannel, get_channel, TextChannel, VoiceChannel, Category
from .user import User
from .role import Role


class Member(User):

    def __init__(self, **data):
        super(Member, self).__init__(**data.get('user'), _client=data.get('_client'))
        self.guild: Guild = data.get('_guild')
        self.nick: Optional[str] = data.get('nick')
        self.roles: Dict[int, Role] = {int(x): self.guild.get_role(int(x)) for x in data.get('roles')}
        self.joined_at = data.get('joined_at')  # FIXME port to datetime
        self.premium_since: Optional[str] = data.get('premium_since')
        self.deaf: bool = data.get('deaf')
        self.mute: bool = data.get('mute')
        self.pending: Optional[bool] = data.get('pending')

    async def add_role(self, role: Union[Role, int], reason: Optional[str] = None):
        await self._client.http.request(Route('PUT',
                                              '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                                              guild_id=self.guild.id,
                                              user_id=self.id,
                                              role_id=role),
                                        reason=reason)

    async def remove_role(self, role: Union[Role, int], reason: Optional[str] = None):
        await self._client.http.request(Route('DELETE',
                                              '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                                              guild_id=self.guild.id,
                                              user_id=self.id,
                                              role_id=role),
                                        reason=reason)

    async def kick(self, reason: Optional[str] = None):
        await self._client.http.request(Route('DELETE',
                                              '/guilds/{guild_id}/members/{user_id}',
                                              guild_id=self.guild.id,
                                              user_id=self.id),
                                        reason=reason)

    async def ban(self, delete_message_days: Optional[int] = 0, reason: Optional[str] = None):
        await self._client.http.request(Route('PUT',
                                              '/guilds/{guild_id}/bans/{user_id}',
                                              guild_id=self.guild.id,
                                              user_id=self.id),
                                        json={'delete_message_days': delete_message_days},
                                        reason=reason)


class Guild(Snowflake):
    
    def __init__(self, **kwargs):
        super(Guild, self).__init__(**kwargs)
        self.name: str = kwargs.get('name')
        # FIXME make its own dynamic class for Images
        self.icon: str = f'https://cdn.discordapp.com/icons/{self.id}/{kwargs.get("icon")}.png'
        self.splash: str = f'https://cdn.discordapp.com/splashes/{self.id}/{kwargs.get("splash")}.png'
        self.discovery_splash: Optional[str] = f'https://cdn.discordapp.com/discovery-splashes/{self.id}/' \
                                               f'{kwargs.get("discovery_splash")}' \
            if kwargs.get("discovery_splash") is not None else None
        self.owner: Optional[bool] = kwargs.get('owner')
        self.owner_id: Snowflake = Snowflake(id=kwargs.get('owner_id'))
        self.afk_channel_id: Optional[Snowflake] = Snowflake(id=kwargs.get('afk_channel_id')) \
            if kwargs.get('afk_channel_id') is not None else None
        self.afk_timeout: int = kwargs.get('afk_timeout')
        self.widget_enabled: Optional[bool] = kwargs.get('widgets_enabled')
        self.widget_channel_id: Optional[Snowflake] = Snowflake(id=kwargs.get('widget_channel_id')) \
            if kwargs.get('widget_channel_id') is not None else None
        self.verification_level: GuildVerificationLevel = GuildVerificationLevel(kwargs.get('verification_level'))
        self.default_message_notifications: MessageNotificationLevel = \
            MessageNotificationLevel(kwargs.get('default_message_notifications'))
        self.explicit_content_filter: ExplicitContentFilterLevel = \
            ExplicitContentFilterLevel(kwargs.get('explicit_content_filter'))
        self.roles: Dict[int, Role] = {int(k.get('id')): Role(**k, _client=self._client) for k in kwargs.get('roles')}
        self.emojis = []  # FIXME parse emojis
        self.features: List[str] = kwargs.get('features')
        self.mfa_level: MFALevel = MFALevel(kwargs.get('mfa_level'))
        self.application_id: Optional[Snowflake] = Snowflake(id=kwargs.get('application_id')) \
            if kwargs.get('application_id') is not None else None
        self.system_channel_id: Optional[Snowflake] = Snowflake(id=kwargs.get('system_channel_id')) \
            if kwargs.get('system_channel_id') is not None else None
        self.system_channel_flags: SystemChannelFlags = SystemChannelFlags(kwargs.get('system_channel_flags'))
        self.rules_channel_id: Optional[Snowflake] = Snowflake(id=kwargs.get('rules_channel_id')) \
            if kwargs.get('rules_channel_id') is not None else None
        self.joined_at: Optional[str] = kwargs.get('joined_at')  # FIXME make datetime
        self.large: Optional[bool] = kwargs.get('large')
        self.unavailable: Optional[bool] = kwargs.get('unavailable')
        self.member_count: Optional[int] = kwargs.get('member_count')
        self._channels: Dict[int, GuildChannel] = {}
        for cd in kwargs.get('channels', []):
            c = get_channel(**cd, _client=self._client, guild_id=self.id)
            self._channels[c.id] = c
        self.threads = []  # FIXME parse threads
        # FIXME parse presences
        self.max_presences: Optional[int] = kwargs.get('max_presences')
        self.max_members: Optional[int] = kwargs.get('max_members')
        self.vanity_url_code: Optional[str] = kwargs.get('vanity_url_code')
        self.description: Optional[str] = kwargs.get('description')
        self.banner: Optional[str] = f'https://cdn.discordapp.com/banners/{self.id}/{kwargs.get("banner")}.png' \
            if kwargs.get("banner") is not None else None
        self.premium_tier: PremiumTier = PremiumTier(kwargs.get('premium_tier'))
        self.premium_subscription_count: Optional[int] = kwargs.get('premium_subscription_count')
        self.preferred_locale: str = kwargs.get('preferred_locale')
        self.public_updates_channel_id: Optional[Snowflake] = Snowflake(id=kwargs.get('public_updates_channel_id')) \
            if kwargs.get('public_updates_channel_id') is not None else None
        self.max_video_channel_users: Optional[int] = kwargs.get('max_video_channel_users')
        self.approximate_member_count: Optional[int] = kwargs.get('approximate_member_count')
        self.approximate_presence_count: Optional[int] = kwargs.get('approximate_presence_count')
        self.welcome_screen = None  # FIXME parse welcome screen
        self.nsfw_level: GuildNSFWLevel = GuildNSFWLevel(kwargs.get('nsfw_level'))
        self.stage_instances = []  # FIXME parse stage instances
        self.stickers = []  # FIXME parse stickers
        self._members: Dict[int, Member] = {}
        for m_d in kwargs.get('members', []):
            m = Member(**m_d, _client=self._client, _guild=self)
            self._members[m.id] = m
            if self._client is not None:
                self._client.add_user_to_cache(m_d.get('user'))

    def get_channel(self, channel_id: Union[Snowflake, int]) -> Optional[Union[GuildChannel, TextChannel, VoiceChannel, Category]]:
        """Get Channel Object from cache if found, otherwise returns None"""
        return self._channels.get(channel_id.id if isinstance(channel_id, Snowflake) else channel_id)

    def get_member(self, member_id: Union[Snowflake, int]) -> Optional[Member]:
        return self._members.get(member_id.id if isinstance(member_id, Snowflake) else member_id)

    async def fetch_member(self, member_id: Union[Snowflake, int]) -> Member:
        data = await self._client.http.request(Route('GET',
                                                     '/guilds/{guild_id}/members/{member_id}',
                                                     guild_id=self.id,
                                                     member_id=member_id))
        member = Member(**data, _client=self._client, _guild=self)
        # override cache
        self._members[member.id] = member
        return member

    def get_role(self, role_id: Union[Snowflake, int]) -> Optional[Role]:
        return self._members.get(role_id.id if isinstance(role_id, Snowflake) else role_id)

    async def fetch_invites(self):
        return await self._client.http.request(Route('GET', '/guilds/{guild_id}/invites', guild_id=self.id))
