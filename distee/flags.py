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
        'DIRECT_MESSAGE_TYPING': 1 << 14
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
