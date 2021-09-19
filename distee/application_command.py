from .utils import Snowflake
from .enums import ApplicationCommandType, ApplicationCommandOptionType
from typing import Optional, List, Union
from .guild import Guild


class ApplicationCommandOptionChoice:
    name: str
    value: Union[str, int, float]

    def __init__(self, **data):
        self.name = data.get('name')
        self.value = data.get('value')


class ApplicationCommandOption:
    type: ApplicationCommandOptionType
    name: str
    description: str
    required: bool = False
    choices: List[ApplicationCommandOptionChoice] = None
    options: List['ApplicationCommandOption'] = None

    def __init__(self, **data):
        self.type = data.get('type')
        self.name = data.get('name')
        self.description = data.get('description')
        self.required = data.get('required')
        self.options = [ApplicationCommandOption(**d) for d in data.get('options')] \
            if data.get('options') is not None else None
        self.choices = [ApplicationCommandOptionChoice(**d) for d in data.get('choices')] \
            if data.get('choices') is not None else None


class ApplicationCommand(Snowflake):
    
    def __init__(self, **data):
        super(ApplicationCommand, self).__init__(**data)
        self.type: ApplicationCommandType = ApplicationCommandType(data.get('type', 1))
        self.application_id: Snowflake = Snowflake(id=data.get('application_id'))
        self.guild_id: Optional[Snowflake] = Snowflake(id=data.get('guild_id')) \
            if data.get('guild_id') is not None else None

        if self._client is not None:
            self.guild: Optional[Guild] = self._client.get_guild(self.guild_id) if self.guild_id is not None else None
        self.name: str = data.get('name')
        self.description: str = data.get('description')
        self.default_permission: bool = data.get('default_permission', True)
        self.version: Snowflake = Snowflake(id=data.get('version'))
        self.options = [ApplicationCommandOption(**d) for d in data.get('options')] \
            if data.get('options') is not None else None

