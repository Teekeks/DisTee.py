from enum import IntFlag
from typing import List


class DisTeeIntFlag(IntFlag):

    pass


class Intents:

    _values = {
        'GUILDS': 1 << 0,
        'GUILD_MEMBERS': 1 << 1,
        'GUILD_BANS': 1 << 2,
        'GUILD_EMOJIS_AND_STICKERS': 1 << 3,
        'GUILD_INTEGRATIONS': 1 << 4,
        'GUILD_WEBHOOKS': 1 << 5,
        'GUILD_INVITES': 1 << 6,
        'GUILD_VOICE_STATES': 1 << 7,
        'GUILD_PRESENCES': 1 << 8,
        'GUILD_MESSAGES': 1 << 9,
        'GUILD_MESSAGE_REACTIONS': 1 << 10,
        'GUILD_MESSAGE_TYPING': 1 << 11,
        'DIRECT_MESSAGES': 1 << 12,
        'DIRECT_MESSAGE_REACTIONS': 1 << 13,
        'DIRECT_MESSAGE_TYPING': 1 << 14,
        'GUILD_SCHEDULED_EVENTS': 1 << 16
    }

    value: int = 0

    @classmethod
    def all(cls) -> 'Intents':
        val = 0
        intents = cls()
        for y in intents._values.values():
            val |= y
        intents.value = val
        return intents

    @classmethod
    def default(cls) -> 'Intents':
        val = cls.all()
        val.value -= val._values['GUILD_PRESENCES'] | val._values['GUILD_MEMBERS']
        return val

    def remove(self, intent: str):
        self.value -= self._values[intent]

    def add(self, intent: str):
        self.value += self._values[intent]


class SystemChannelFlags(IntFlag):
    SUPPRESS_JOIN_NOTIFICATIONS = 1 << 0
    SUPPRESS_PREMIUM_SUBSCRIPTIONS = 1 << 1
    SUPPRESS_GUILD_REMINDER_NOTIFICATIONS = 1 << 2


class UserFlags(IntFlag):
    NONE = 0
    DISCORD_EMPLOYEE = 1 << 0
    PARTNERED_SERVER_OWNER = 1 << 1
    HYPE_SQUAD_EVENTS = 1 << 2
    BUG_HUNTER_LEVEL_1 = 1 << 3
    HOUSE_BRAVERY = 1 << 6
    HOUSE_BRILLIANCE = 1 << 7
    HOUSE_BALANCE = 1 << 8
    EARLY_SUPPORTER = 1 << 9
    TEAM_USER = 1 << 10
    BUG_HUNTER_LEVEL_2 = 1 << 14
    VERIFIED_BOT = 1 << 16
    EARLY_VERIFIED_BOT_DEVELOPER = 1 << 17
    DISCORD_CERTIFIED_MODERATOR = 1 << 18


class InteractionCallbackFlags(IntFlag):
    EPHEMERAL = 1 << 6


class Permissions(IntFlag):
    CREATE_INSTANT_INVITE = 1 << 0
    KICK_MEMBERS = 1 << 1
    BAN_MEMBERS = 1 << 2
    ADMINISTRATOR = 1 << 3
    MANAGE_CHANNELS = 1 << 4
    MANAGE_GUILD = 1 << 5
    ADD_REACTIONS = 1 << 6
    VIEW_AUDIT_LOG = 1 << 7
    PRIORITY_SPEAKER = 1 << 8
    STREAM = 1 << 9
    VIEW_CHANNEL = 1 << 10
    SEND_MESSAGES = 1 << 11
    SEND_TTS_MESSAGES = 1 << 12
    MANAGE_MESSAGES = 1 << 13
    EMBED_LINKS = 1 << 14
    ATTACH_FILES = 1 << 15
    READ_MESSAGE_HISTORY = 1 << 16
    MENTION_EVERYONE = 1 << 17
    USE_EXTERNAL_EMOJIS = 1 << 18
    VIEW_GUILD_INSIGHTS = 1 << 19
    CONNECT = 1 << 20
    SPEAK = 1 << 21
    MUTE_MEMBERS = 1 << 22
    DEAFEN_MEMBERS = 1 << 23
    MOVE_MEMBERS = 1 << 24
    USE_VAD = 1 << 25
    CHANGE_NICKNAME = 1 << 26
    MANAGE_NICKNAMES = 1 << 27
    MANAGE_ROLES = 1 << 28
    MANAGE_WEBHOOKS = 1 << 29
    MANAGE_EMOJIS_AND_STICKERS = 1 << 30
    USE_APPLICATION_COMMANDS = 1 << 31
    REQUEST_TO_SPEAK = 1 << 32
    MANAGE_THREADS = 1 << 34
    CREATE_PUBLIC_THREADS = 1 << 35
    CREATE_PRIVATE_THREADS = 1 << 36
    USE_EXTERNAL_STICKERS = 1 << 37
    SEND_MESSAGES_IN_THREADS = 1 << 38
    START_EMBEDDED_ACTIVITIES = 1 << 39
    MODERATE_MEMBERS = 1 << 40

    def values(self):
        return [flag for flag in Permissions if flag in self]
