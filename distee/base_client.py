import asyncio
import logging
from typing import Union, List, Optional, Callable, Awaitable, Dict

from distee.application import Application
from distee.application_command import ApplicationCommand
from distee.enums import InteractionType
from distee.errors import ClientException
from distee.guild import Guild
from distee.http import HTTPClient
from distee.interaction import Interaction
from distee.route import Route
from distee.user import User
from distee.utils import command_lists_equal, Snowflake
import re


INTER_REGEX = re.compile(r'^([a-zA-Z0-9_]+)_([a-zA-Z0-9|]+)$')


class BaseClient:

    _application_commands: Dict[int, ApplicationCommand] = {}
    _interaction_handler: Dict[str, Callable] = {}
    _autocomplete_handler: Dict[str, Callable] = {}
    _command_registrar: List[Dict] = []
    _default_command_preprocessors = []
    http: HTTPClient
    user: User = None
    interaction_listener = None
    command_listener = None
    interaction_error_listener = None

    def __init__(self):
        self.http = HTTPClient(self)
        self.application: Application = None

    async def login(self, token):
        data = await self.http.do_login(token)
        if data is None:
            raise ClientException('Failed to log in')
        self.user = User(**data)
        logging.debug(f'Logged in as user {self.user.username}#{self.user.discriminator}')

    async def _on_interaction_create(self, data: dict):
        interaction = None
        try:
            interaction = Interaction(**data, _client=self)
            _id = interaction.data.id
            if interaction.type == InteractionType.APPLICATION_COMMAND:
                ac = self._application_commands.get(_id)
                if ac is None:
                    logging.error(f'could not find callback for command {interaction.data.name} ({_id})')
                    return
                for dcpp in self._default_command_preprocessors:
                    if not await dcpp(interaction):
                        return
                # FIXME use command specific preprocessor
                if self.command_listener is not None:
                    asyncio.ensure_future(self.command_listener(ac, interaction))
                await ac.callback(interaction)
            elif interaction.type in (InteractionType.MESSAGE_COMPONENT, InteractionType.MODAL_SUBMIT):
                if self.interaction_listener is not None:
                    asyncio.ensure_future(self.interaction_listener(interaction))
                ac = self._interaction_handler.get(interaction.data.custom_id)
                if ac is None:
                    # check if var interaction exists
                    match = INTER_REGEX.fullmatch(interaction.data.custom_id)
                    if match is not None:
                        interaction.custom_id_var = match[2]
                        ac = self._interaction_handler.get(match[1] + '_{var}')
                if ac is None:
                    logging.exception(f'could not find handler for interaction with custom id {interaction.data.custom_id}')
                    return
                await ac(interaction)
            elif interaction.type == InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
                ac = self._autocomplete_handler.get(interaction.data.name)
                if ac is None:
                    logging.error(f'could not find autocomplete handler for command {interaction.data.name} ({interaction.data.id}')
                    return
                await ac(interaction)
        except Exception as e:
            logging.exception('Exception while handling interaction:')
            if self.interaction_error_listener is not None:
                try:
                    await self.interaction_error_listener(interaction, e)
                except:
                    logging.exception('Exception in interaction exception handler while handling a exception')

    ########################################################################################################################
    # Command registration
    ########################################################################################################################

    async def _register_global_commands(self):
        # register global commands
        globals_to_override = []
        for c in self._command_registrar:
            if not c.get('global'):
                continue
            globals_to_override.append(c.get('ap'))

        _remote = [ApplicationCommand(**d, _client=self) for d in await self.http.request(Route(
            'GET', f'/applications/{self.application.id}/commands'))]
        if not command_lists_equal(globals_to_override, _remote):
            _remote = [
                ApplicationCommand(**x, _client=self) for x in await self.http.request(Route(
                    'PUT', f'/applications/{self.application.id}/commands'),
                    json=[g.get_json_data() for g in globals_to_override])]
        for ap in _remote:
            callback = None
            for c in self._command_registrar:
                if not c.get('global'):
                    continue
                if c.get('ap').name == ap.name and c.get('ap').type == ap.type:
                    callback = c.get('callback')
                    break
            ap.callback = callback
            self._application_commands[ap.id] = ap

    def register_command(self,
                         ap: ApplicationCommand,
                         callback,
                         is_global: bool,
                         guild_filter: Union[int, None, List[int]],
                         preprocessors: Optional[List[Callable[[Interaction], Awaitable[bool]]]] = None):
        if is_global:
            # register global command
            self._command_registrar.append({
                'ap': ap,
                'callback': callback,
                'global': True,
                'prep': preprocessors
            })
        else:
            # register internally for server specific
            self._command_registrar.append({
                'ap': ap,
                'global': False,
                'guild_filter': guild_filter,
                'callback': callback,
                'prep': preprocessors
            })

    def add_default_command_preprocessor(self, com):
        self._default_command_preprocessors.append(com)
    pass

    async def fetch_bot_application_information(self) -> Application:
        data = await self.http.request(Route('GET', '/oauth2/applications/@me'))
        self.application = Application(**data, _client=self)
        return self.application

    async def fetch_global_application_commands(self) -> List[ApplicationCommand]:
        data = await self.http.request(Route('GET', f'/applications/{self.application.id}/commands'))
        return [ApplicationCommand(**d, _client=self) for d in data]

    async def fetch_guild_application_commands(self, gid: int) -> List[ApplicationCommand]:
        data = await self.http.request(Route('GET',
                                             f'/applications/{self.application.id}/guilds/{gid}/commands',
                                             guild_id=gid))
        return [ApplicationCommand(**d, _client=self) for d in data]

    async def fetch_guild(self, s: Union[Snowflake, int]) -> Guild:
        data = await self.http.request(Route('GET', '/guilds/{guild_id}', guild_id=s))
        return Guild(**data, _client=self)

    async def fetch_user(self, uid: Union[Snowflake, int]) -> User:
        data = await self.http.request(Route('GET', '/users/{user_id}', user_id=uid))
        user = User(**data, _client=self)
        return user

    def get_guild(self, s: Union[Snowflake, int]) -> Optional[Guild]:
        return None

    def get_user(self, s: Union[Snowflake, int]) -> Optional[User]:
        return None

######################################################################################################################################################
# DECORATOR
######################################################################################################################################################

    def interaction_handler(self,
                            custom_id: Optional[str] = None):
        def decorator(func):
            self._interaction_handler[custom_id] = func
            return func
        return decorator

    def autocomplete_handler(self,
                             command_name: str):
        def decorator(func):
            self._autocomplete_handler[command_name] = func
            return func
        return decorator
