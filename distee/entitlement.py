from .utils import Snowflake, snowflake_or_none
from typing import Optional


__all__ = ['Entitlement']


class Entitlement(Snowflake):

    def __init__(self, **data):
        super().__init__(**data)
        self.sku_id: Snowflake = snowflake_or_none(data.get('sku_id'))
        self.application_id: Snowflake = snowflake_or_none(data.get('application_id'))
        self.user_id: Optional[Snowflake] = snowflake_or_none(data.get('user_id'))
        self.type: int = data.get('type')
        self.deleted: bool = data.get('deleted')
        self.starts_at: Optional[str] = data.get('starts_at')
        self.ends_at: Optional[str] = data.get('ends_at')
        self.guild_id: Optional[Snowflake] = snowflake_or_none(data.get('guild_id'))
