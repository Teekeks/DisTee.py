from enum import IntEnum, Enum


class GuildVerificationLevel(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


class MessageNotificationLevel(IntEnum):
    ALL_MESSAGES = 0
    ONLY_MENTIONS = 1


class ExplicitContentFilterLevel(IntEnum):
    DISABLED = 0
    MEMBERS_WITHOUT_ROLES = 1
    ALL_MEMBERS = 2


class MFALevel(IntEnum):
    NONE = 0
    ELEVATED = 1


class PremiumTier(IntEnum):
    NONE = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class GuildNSFWLevel(IntEnum):
    DEFAULT = 0
    EXPLICIT = 1
    SAFE = 2
    AGE_RESTRICTED = 3


class ChannelType(IntEnum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
    GUILD_STORE = 6
    GUILD_NEWS_THREAD = 10
    GUILD_PUBLIC_THREAD = 11
    GUILD_PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13


class ApplicationCommandType(IntEnum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


class ComponentType(IntEnum):
    ACTION_ROW = 1
    BUTTON = 2
    SELECT_MENU = 3


class ApplicationCommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10


class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4


class InteractionResponseType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    MODAL = 9


class Event(Enum):
    READY = 'ready'

    GUILD_JOINED = 'guild_joined'
    GUILD_LEFT = 'guild_left'
    MEMBER_JOINED = 'member_joined'
    MEMBER_UPDATED = 'member_updated'

    GUILD_UPDATED = 'guild_updated'
    GUILD_ROLE_CREATED = 'guild_role_created'
    GUILD_ROLE_DELETED = 'guild_role_deleted'
    GUILD_ROLE_UPDATED = 'guild_role_updated'

    MESSAGE_SEND = 'message_send'
