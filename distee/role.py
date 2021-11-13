from .flags import Permissions
from .utils import Snowflake
from typing import Optional


class RoleTag:
    def __init__(self, **data):
        self.bot_id: Optional[Snowflake] = Snowflake(id=data.get('bot_id')) if data.get('bot_id') is not None else None
        self.integration_id: Optional[Snowflake] = Snowflake(id=data.get('integration_id')) \
            if data.get('integration_id') is not None else None
        self.premium_subscriber = data.get('premium_subscriber')


class Role(Snowflake):
    
    def __init__(self, **data):
        super(Role, self).__init__(**data)
        self.name: str = data.get('name')
        self.color: int = data.get('color')
        self.hoist: bool = data.get('hoist')
        self.position: int = data.get('position')
        self.raw_permissions: str = data.get('permissions')
        self.permissions: Permissions = Permissions(int(self.raw_permissions))
        self.managed: bool = data.get('managed')
        self.mentionable: bool = data.get('mentionable')
        self.tags: Optional[RoleTag] = RoleTag(**data.get('tags')) if data.get('tags') is not None else None


