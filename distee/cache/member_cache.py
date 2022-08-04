from typing import Union, Optional, TYPE_CHECKING
from distee.utils import snowflake_id

if TYPE_CHECKING:
    from distee.cache import BaseMemberCache
    from distee.guild import Member
    from distee.utils import Snowflake


class NoMemberCache(BaseMemberCache):
    async def member_added(self, member: Member):
        pass

    async def member_updated(self, member: Member) -> Optional[Member]:
        return None

    async def member_removed(self, guild_id: Union[int, Snowflake], member_id: Union[int, Snowflake]) -> Optional[Member]:
        return None

    async def get_member(self, guild_id: Union[int, Snowflake], member_id: Union[int, Snowflake]) -> Optional[Member]:
        return None


class RamMemberCache(BaseMemberCache):
    """Strategy: keep all members of a guild cached till they are removed from said guild"""

    def __init__(self):
        self.cache = {}

    def _ensure_guild(self, gid: int):
        if self.cache.get(gid) is None:
            self.cache[gid] = {}

    async def member_added(self, member: Member):
        self._ensure_guild(member.guild.id)
        self.cache[member.guild.id][member.id] = member

    async def member_updated(self, member: Member) -> Optional[Member]:
        self._ensure_guild(member.guild.id)
        before = self.cache[member.guild.id].get(member.id)
        self.cache[member.guild.id][member.id] = member
        return before

    async def member_removed(self, guild_id: Union[int, Snowflake], member_id: Union[int, Snowflake]) -> Optional[Member]:
        gid = snowflake_id(guild_id)
        if self.cache.get(gid) is None:
            return None
        mid = snowflake_id(member_id)
        return self.cache[gid].pop(mid, None)

    async def get_member(self, guild_id: Union[int, Snowflake], member_id: Union[int, Snowflake]) -> Optional[Member]:
        gid = snowflake_id(guild_id)
        if self.cache.get(gid) is None:
            return None
        mid = snowflake_id(member_id)
        return self.cache[gid].get(mid)
