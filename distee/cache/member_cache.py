import asyncio
import datetime
import logging
import time
from typing import Union, Optional, TYPE_CHECKING, List, Dict
from distee.utils import snowflake_id
from distee.cache import BaseMemberCache

if TYPE_CHECKING:
    from distee.guild import Member
    from distee.utils import Snowflake


class NoMemberCache(BaseMemberCache):
    async def get_guild_members(self, guild_id: Union[int, 'Snowflake']) -> List['Member']:
        return []

    async def guild_left(self, guild_id: Union[int, 'Snowflake']):
        pass

    async def member_added(self, member: 'Member'):
        pass

    async def member_updated(self, member: 'Member') -> Optional['Member']:
        return None

    async def member_removed(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        return None

    async def get_member(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        return None


class RamMemberCache(BaseMemberCache):
    """Strategy: keep all members of a guild cached till they are removed from said guild"""

    async def get_guild_members(self, guild_id: Union[int, 'Snowflake']) -> List['Member']:
        return self.cache.get(snowflake_id(guild_id), [])

    def __init__(self):
        self.cache = {}

    def _ensure_guild(self, gid: int):
        if self.cache.get(gid) is None:
            self.cache[gid] = {}

    async def guild_left(self, guild_id: Union[int, 'Snowflake']):
        self.cache.pop(snowflake_id(guild_id))

    async def member_added(self, member: 'Member'):
        self._ensure_guild(member.guild.id)
        self.cache[member.guild.id][member.id] = member

    async def member_updated(self, member: 'Member') -> Optional['Member']:
        self._ensure_guild(member.guild.id)
        before = self.cache[member.guild.id].get(member.id)
        self.cache[member.guild.id][member.id] = member
        return before

    async def member_removed(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        gid = snowflake_id(guild_id)
        if self.cache.get(gid) is None:
            return None
        mid = snowflake_id(member_id)
        return self.cache[gid].pop(mid, None)

    async def get_member(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        gid = snowflake_id(guild_id)
        if self.cache.get(gid) is None:
            return None
        mid = snowflake_id(member_id)
        return self.cache[gid].get(mid)


class TimedRamMemberCache(BaseMemberCache):
    """Strategy: Cache all members who where active in the last x seconds"""

    async def get_guild_members(self, guild_id: Union[int, 'Snowflake']) -> List['Member']:
        return self.cache.get(snowflake_id(guild_id), [])

    def __init__(self, seconds_cached: int, client):
        self.seconds_cached: int = seconds_cached
        asyncio.ensure_future(self._cleanup_task(), loop=client.loop)
        self.cache = {}
        self.touched: Dict[int, Dict[int, int]] = {}

    def _ensure_guild(self, gid: int):
        if self.cache.get(gid) is None:
            self.cache[gid] = {}

    def _touch(self, gid, mid):
        t = int(time.time() * 1000)
        if self.touched.get(gid) is None:
            self.touched[gid] = {}
        self.touched[gid][mid] = t

    async def _cleanup_task(self):
        while True:
            self._cleanup()
            await asyncio.sleep(5)

    def _cleanup(self):
        tc = int(time.time() * 1000) - (self.seconds_cached * 1000)
        for gid, gd in self.touched.items():
            for mid in list(gd):
                t = gd[mid]
                if t < tc:
                    logging.debug(f'member {mid} in {gid} cache cleared')
                    self.touched.get(gid, {}).pop(mid)
                    self.cache.get(gid, {}).pop(mid)

    async def guild_left(self, guild_id: Union[int, 'Snowflake']):
        self.cache.pop(snowflake_id(guild_id))
        self.touched.pop(snowflake_id(guild_id))

    async def member_added(self, member: 'Member'):
        self._ensure_guild(member.guild.id)
        self.cache[member.guild.id][member.id] = member
        self._touch(member.guild.id, member.id)

    async def member_updated(self, member: 'Member') -> Optional['Member']:
        self._ensure_guild(member.guild.id)
        before = self.cache[member.guild.id].get(member.id)
        self.cache[member.guild.id][member.id] = member
        self._touch(member.guild.id, member.id)
        return before

    async def member_removed(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        gid = snowflake_id(guild_id)
        if self.cache.get(gid) is None:
            return None
        mid = snowflake_id(member_id)
        return self.cache[gid].pop(mid, None)

    async def get_member(self, guild_id: Union[int, 'Snowflake'], member_id: Union[int, 'Snowflake']) -> Optional['Member']:
        gid = snowflake_id(guild_id)
        if self.cache.get(gid) is None:
            return None
        mid = snowflake_id(member_id)
        self._touch(gid, mid)
        return self.cache[gid].get(mid)
