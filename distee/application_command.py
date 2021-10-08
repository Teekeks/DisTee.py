from .utils import Snowflake
from .enums import ApplicationCommandType, ApplicationCommandOptionType
from typing import Optional, List, Union
from .guild import Guild
from .http import Route


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
            if data.get('options') is not None else []
        self.choices = [ApplicationCommandOptionChoice(**d) for d in data.get('choices')] \
            if data.get('choices') is not None else []

    def get_json_data(self):
        return {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'required': self.required,
            'options': [d.get_json_data() for d in self.options],
            'choices': [{'name': d.name, 'value': d.value} for d in self.choices]
        }


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
            if data.get('options') is not None else []
        self.callback = data.get('_callback')

    def get_json_data(self):
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'options': [d.get_json_data() for d in self.options]
        }

    def is_global(self):
        return self.guild_id is None

    async def delete(self):
        if self.is_global():
            await self._client.http.request(Route('DELETE',
                                                  f'/applications/{self.application_id.id}/commands/{self.id}'))
        else:
            await self._client.http.request(Route('DELETE',
                                                  '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
                                                  application_id=self.application_id,
                                                  guild_id=self.guild_id,
                                                  command_id=self.id))

