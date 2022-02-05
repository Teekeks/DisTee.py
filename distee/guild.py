from datetime import datetime, timedelta
import logging
import typing

from .route import Route
from .utils import Snowflake
from typing import Optional, List, Dict, Union
from .enums import GuildVerificationLevel, MessageNotificationLevel, ExplicitContentFilterLevel, MFALevel, PremiumTier
from .enums import GuildNSFWLevel
from .flags import SystemChannelFlags
from .channel import get_channel
from .user import User
from .role import Role

if typing.TYPE_CHECKING:
    from .channel import GuildChannel, TextChannel, VoiceChannel, Category
    from .client import Client


class Member(User):

    __slots__ = [
        'guild',
        'nick',
        'roles',
        'joined_at',
        'deaf',
        'mute',
        'pending',
        'communication_disabled_until',
        'premium_since'
    ]

    def __init__(self, **data):
        super(Member, self).__init__(**data.get('user'), _client=data.get('_client'))
        self.guild: Guild = data.get('_guild')
        self.nick: Optional[str] = data.get('nick')
        self.roles: Dict[int, Role] = {int(x): self.guild.get_role(int(x)) for x in data.get('roles')} if self.guild is not None else {}
        self.joined_at = data.get('joined_at')  # FIXME port to datetime
        self.premium_since: Optional[str] = data.get('premium_since')
        self.deaf: bool = data.get('deaf')
        self.mute: bool = data.get('mute')
        self.pending: Optional[bool] = data.get('pending')
        self.communication_disabled_until: Optional[datetime] = datetime.fromisoformat(data.get('communication_disabled_until')) \
            if data.get('communication_disabled_until') is not None else None

    @property
    def display_name(self):
        """The name the user has on the server, uses nick if set otherwise username"""
        return self.nick if self.nick is not None else self.username

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

    async def add_roles(self, roles: List[Union[Role, int]], reason: Optional[str] = None):
        """Add multiple roles in one API call, fall back to safer method if only one is added"""
        if len(roles) == 1:
            await self.add_role(roles[0], reason)
            return
        if len(roles) == 0:
            raise ValueError('at least 1 role needs to be specified')
        target = list(set(list(self.roles.keys()) + [r if isinstance(r, int) else r.id for r in roles]))
        await self._client.http.request(Route('PATCH',
                                              '/guilds/{guild_id}/members/{user_id}',
                                              guild_id=self.guild,
                                              user_id=self.id),
                                        json={'roles': target},
                                        reason=reason)

    async def remove_roles(self, roles: List[Union[Role, int]], reason: Optional[str] = None):
        """Remove multiple roles in one API call, fall back to safer method if only one is removed"""
        if len(roles) == 1:
            await self.remove_role(roles[0], reason)
            return
        if len(roles) == 0:
            raise ValueError('at least 1 role needs to be specified')
        rem = [r if isinstance(r, int) else r.id for r in roles]
        target = [r for r in self.roles.keys() if r not in rem]
        await self._client.http.request(Route('PATCH',
                                              '/guilds/{guild_id}/members/{user_id}',
                                              guild_id=self.guild,
                                              user_id=self.id),
                                        json={'roles': target},
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

    @property
    def in_timeout(self) -> bool:
        return self.communication_disabled_until is not None and self.communication_disabled_until > datetime.utcnow()

    async def timeout(self, seconds: int, reason: Optional[str] = None):
        time = datetime.utcnow() + timedelta(seconds=seconds)
        js = {'communication_disabled_until': time.isoformat()}
        await self._client.http.request(Route('PATCH',
                                              '/guilds/{guild_id}/members/{member_id}',
                                              guild_id=self.guild,
                                              member_id=self),
                                        json=js,
                                        reason=reason)

    async def reset_timeout(self, reason: Optional[str] = None):
        await self._client.http.request(Route('PATCH',
                                              '/guilds/{guild_id}/members/{member_id}',
                                              guild_id=self.guild,
                                              member_id=self),
                                        json={'communication_disabled_until': None},
                                        reason=reason)

    def get_highest_role(self) -> Role:
        highest = None
        for r in self.roles.values():
            if highest is None or highest.position < r.position:
                highest = r
        return highest


class VoiceState:

    __slots__ = [
        'guild',
        '_client',
        'channel_id',
        'user_id',
        'session_id',
        'deaf',
        'mute',
        'self_deaf',
        'self_mute',
        'self_stream',
        'self_video',
        'request_to_speak_timestamp'
    ]

    def __init__(self, **data):
        self.guild: 'Guild' = data.get('_guild')
        self._client: 'Client' = data.get('_client')
        self.from_data(**data)

    def from_data(self, **data):
        self.channel_id: Snowflake = Snowflake(id=data.get('channel_id'))
        self.user_id: Snowflake = Snowflake(id=data.get('user_id'))
        self.session_id: str = data.get('session_id')
        self.deaf: bool = data.get('deaf')
        self.mute: bool = data.get('mute')
        self.self_deaf: bool = data.get('self_deaf')
        self.self_mute: bool = data.get('self_mute')
        self.self_stream: bool = data.get('self_stream', False)
        self.self_video: bool = data.get('self_video')
        self.request_to_speak_timestamp: str = data.get('request_to_speak_timestamp')


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
        self.roles: Dict[int, Role] = {int(k.get('id')): Role(**k, _client=self._client, _guild=self) for k in kwargs.get('roles')}
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
        self._channels: Dict[int, 'GuildChannel'] = {}
        for cd in kwargs.get('channels', []):
            c = get_channel(**cd, _client=self._client, guild_id=self.id)
            self._channels[c.id] = c
        self.threads = []  # FIXME parse threads
        # FIXME parse presences
        self.voice_states: Dict[int, VoiceState] = {
            int(d.get('user_id')): VoiceState(**d, _client=self._client, _guild=self)
            for d in kwargs.get('voice_states', [])}
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
                if self._client.build_user_cache:
                    self._client.add_user_to_cache(m_d.get('user'))

    @property
    def members(self) -> Dict[int, Member]:
        return self._members

    async def handle_channel_create(self, data: dict):
        channel = get_channel(**data, _client=self._client, _guild=self)
        self._channels[channel.id] = channel

    async def handle_channel_update(self, data: dict):
        channel = get_channel(**data, _client=self._client, _guild=self)
        self._channels[channel.id] = channel

    async def handle_channel_delete(self, data: dict):
        self._channels.pop(int(data['id']))

    async def handle_member_chunk(self, data: dict):
        for m_data in data['members']:
            m = Member(**m_data, _client=self._client, _guild=self)
            self._members[m.id] = m
        if data['chunk_index'] == (data['chunk_count'] - 1):
            logging.info(f'filled member cache for guild {self.id}: got {len(self._members.keys())} members')

    def handle_guild_update(self, **kwargs):
        self.name = kwargs.get('name')
        self.icon: str = f'https://cdn.discordapp.com/icons/{self.id}/{kwargs.get("icon")}.png'
        self.splash: str = f'https://cdn.discordapp.com/splashes/{self.id}/{kwargs.get("splash")}.png'
        self.discovery_splash: Optional[str] = f'https://cdn.discordapp.com/discovery-splashes/{self.id}/' \
                                               f'{kwargs.get("discovery_splash")}' \
            if kwargs.get("discovery_splash") is not None else None
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
        self.roles: Dict[int, Role] = {int(k.get('id')): Role(**k, _client=self._client, _guild=self) for k in kwargs.get('roles')}
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
        self.stickers = []  # FIXME parse stickers

    def get_channel(self, channel_id: Union[Snowflake, int]) -> Optional[Union['GuildChannel', 'TextChannel', 'VoiceChannel', 'Category']]:
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

    async def obtain_member(self, member_id: Union[Snowflake, int]) -> Member:
        """Either get from cache or fetch if not in cache"""
        m = self.get_member(member_id)
        if m is None:
            return await self.fetch_member(member_id)
        return m

    def get_role(self, role_id: Union[Snowflake, int]) -> Optional[Role]:
        return self.roles.get(role_id.id if isinstance(role_id, Snowflake) else role_id)

    async def fetch_invites(self):
        return await self._client.http.request(Route('GET', '/guilds/{guild_id}/invites', guild_id=self.id))

    async def leave_guild(self):
        await self._client.http.request(Route('DELETE', '/users/@me/guilds/{guild_id}', guild_id=self.id))

    def get_self(self) -> Member:
        return self._members[self._client.user.id]
