from .utils import Snowflake
from .enums import ApplicationCommandType, ApplicationCommandOptionType, ChannelType
from typing import Optional, List, Union, TYPE_CHECKING
from .guild import Guild
from .route import Route


class ApplicationCommandOptionChoice:

    __slots__ = [
        'name',
        'value'
    ]

    name: str
    value: Union[str, int, float]

    def __init__(self, **data):
        self.name = data.get('name')
        self.value = data.get('value')

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandOptionChoice):
            return False
        if self.name != other.name or self.value != other.value:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class ApplicationCommandOption:

    __slots__ = [
        'type',
        'name',
        'description',
        'required',
        'choices',
        'options',
        'channel_types'
    ]

    type: ApplicationCommandOptionType
    name: str
    description: str
    required: bool
    choices: List[ApplicationCommandOptionChoice]
    options: List['ApplicationCommandOption']
    channel_types: List[ChannelType]

    def __init__(self, **data):
        self.type = data.get('type')
        self.name = data.get('name')
        self.description = data.get('description')
        self.required = data.get('required', False)
        self.channel_types = data.get('channel_types')
        if data.get('options') is None or len(data.get('options')) == 0:
            self.options: List[ApplicationCommandOption] = []
        elif isinstance(data.get('options')[0], ApplicationCommandOption):
            self.options: List[ApplicationCommandOption] = data.get('options')
        else:
            self.options: List[ApplicationCommandOption] = [ApplicationCommandOption(**d) for d in data.get('options')]

        if data.get('choices') is None or len(data.get('choices')) == 0:
            self.choices: List[ApplicationCommandOptionChoice] = []
        elif isinstance(data.get('choices')[0], ApplicationCommandOptionChoice):
            self.choices: List[ApplicationCommandOptionChoice] = data.get('choices')
        else:
            self.choices: List[ApplicationCommandOptionChoice] = [ApplicationCommandOptionChoice(**d) for d in data.get('choices')]

    def get_json_data(self):
        dat = {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'required': self.required,
            'options': [d.get_json_data() for d in self.options],
            'choices': [{'name': d.name, 'value': d.value} for d in self.choices]
        }
        if self.channel_types is not None and len(self.channel_types) > 0:
            dat['channel_types'] = [i.value for i in self.channel_types]
        return dat

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandOption):
            return False
        if self.type != other.type or self.name != other.name or self.description != other.description or \
                self.required != other.required:
            return False
        if len(self.options) != len(other.options):
            return False
        if self.channel_types != other.channel_types:
            return False
        for i in range(len(self.options)):
            if self.options[i] != other.options[i]:
                return False
        if len(self.choices) != len(other.choices):
            return False
        for i in range(len(self.choices)):
            if self.choices[i] != other.choices[i]:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class ApplicationCommand(Snowflake):

    __slots__ = [
        'type',
        'application_id',
        'guild_id',
        'guild',
        'name',
        'description',
        'default_permission',
        'dm_permission',
        'default_member_permissions',
        'version',
        'options',
        'callback'
    ]

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
        self.dm_permission: bool = data.get('dm_permission', None)
        self.default_member_permissions: str = data.get('default_member_permissions', None)
        self.version: Snowflake = Snowflake(id=data.get('version'))
        if data.get('options') is None or len(data.get('options')) == 0:
            self.options: List[ApplicationCommandOption] = []
        elif isinstance(data.get('options')[0], ApplicationCommandOption):
            self.options: List[ApplicationCommandOption] = data.get('options')
        else:
            self.options: List[ApplicationCommandOption] = [ApplicationCommandOption(**d) for d in data.get('options')]
        self.callback = data.get('_callback')

    def get_json_data(self):
        ret = {
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            # 'default_permission': self.default_permission,
            'options': [d.get_json_data() for d in self.options]
        }
        if self.dm_permission is not None:
            ret['dm_permission'] = self.dm_permission
        if self.default_member_permissions is not None:
            ret['default_member_permissions'] = self.default_member_permissions
        # do not pass the description if its a suer or message command
        if self.type in (ApplicationCommandType.USER, ApplicationCommandType.MESSAGE):
            ret.pop('description', None)
            ret.pop('options', None)
        return ret

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

    async def set_permissions(self, guild: Union[Snowflake, int], permissions: List[dict]):
        await self._client.http.request(Route('PUT',
                                              '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
                                              application_id=self.application_id,
                                              guild_id=guild,
                                              command_id=self.id),
                                        json={'permissions': permissions})

    async def fetch_permissions(self, guild: Union[Snowflake, int]) -> List[dict]:
        data = await self._client.http.request(Route('GET',
                                                     '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
                                                     application_id=self.application_id,
                                                     guild_id=guild,
                                                     command_id=self.id))
        return data.get('permissions', [])

    def __eq__(self, other: 'ApplicationCommand'):
        if not isinstance(other, ApplicationCommand):
            return False
        if self.type != other.type:
            return False
        if self.name != other.name:
            return False
        if (self.description if self.description is not None else '') != (other.description if other.description is not None else ''):
            return False
        if len(self.options) != len(other.options):
            return False
        for i in range(len(self.options)):
            if self.options[i] != other.options[i]:
                return False
        if self.default_permission != other.default_permission:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)




