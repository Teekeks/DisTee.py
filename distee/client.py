import asyncio
import logging
import signal
from copy import deepcopy
from typing import Callable, Awaitable, Optional, Union, List, TypedDict, Dict

import aiohttp

from .gateway import DiscordWebSocket
from .role import Role
from .user import User
from .http import HTTPClient, Route
from .errors import ClientException, ReconnectWebSocket, ConnectionClosed
from .message import Message
from .utils import Snowflake
from .flags import Intents
from .enums import InteractionType, Event, ApplicationCommandType
from .guild import Guild, Member, VoiceState
from .application_command import ApplicationCommand
from .application import Application
from .interaction import Interaction


def _cancel_tasks(loop: asyncio.AbstractEventLoop) -> None:
    tasks = {t for t in asyncio.all_tasks(loop=loop) if not t.done()}

    if not tasks:
        return

    logging.info('Cleaning up after %d tasks.', len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    logging.info('All tasks finished cancelling.')

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during Client.run shutdown.',
                'exception': task.exception(),
                'task': task
            })


def _cleanup_loop(loop: asyncio.AbstractEventLoop) -> None:
    try:
        _cancel_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        logging.info('Closing the event loop.')
        loop.close()


class Client:

    ws: DiscordWebSocket = None
    user: User = None
    http: HTTPClient
    loop = None
    _closed = False
    _raw_gateway_listener = {}
    _event_listener = {}
    _guilds = {}
    _users = {}
    messages = []
    message_cache_size: int = 10
    _application_commands: Dict[int, ApplicationCommand] = {}
    _interaction_handler: Dict[str, Callable] = {}
    _command_registrar: List[Dict] = []
    gateway_listener = None
    interaction_listener = None
    command_listener = None

    def __init__(self):
        self.ws = None
        self.http = HTTPClient()
        self.loop = asyncio.get_event_loop()
        self.intents: Intents = None
        self.application: Application = None
        self.register_raw_gateway_event_listener('MESSAGE_CREATE', self._on_message)
        self.register_raw_gateway_event_listener('GUILD_CREATE', self._on_guild_create)
        self.register_raw_gateway_event_listener('GUILD_MEMBER_ADD', self._on_member_join)
        self.register_raw_gateway_event_listener('READY', self._on_ready)
        self.register_raw_gateway_event_listener('INTERACTION_CREATE', self._on_interaction_create)
        self.register_raw_gateway_event_listener('GUILD_DELETE', self._on_guild_delete)
        self.register_raw_gateway_event_listener('GUILD_MEMBER_UPDATE', self._on_guild_member_update)
        self.register_raw_gateway_event_listener('GUILD_UPDATE', self._on_guild_update)
        self.register_raw_gateway_event_listener('GUILD_ROLE_CREATE', self._on_guild_role_create)
        self.register_raw_gateway_event_listener('GUILD_ROLE_DELETE', self._on_guild_role_delete)
        self.register_raw_gateway_event_listener('GUILD_ROLE_UPDATE', self._on_guild_role_update)
        self.register_raw_gateway_event_listener('VOICE_STATE_UPDATE', self._on_voice_state_update)

    def is_closed(self) -> bool:
        """Returns whether or not this client is closing down"""
        return self._closed

    async def login(self, token):
        data = await self.http.do_login(token)
        if data is None:
            raise ClientException('Failed to log in')
        self.user = User(**data)
        logging.debug(f'Logged in as user {self.user.username}#{self.user.discriminator}')

########################################################################################################################
# EVENT HOOKS
########################################################################################################################

    async def _on_voice_state_update(self, data: dict):
        guild = self.get_guild(int(data.get('guild_id')))
        usr_id = int(data.get('user_id'))
        current = guild.voice_states.get(usr_id)
        if current is None:
            # add new
            vs = VoiceState(**data, _guild=guild, _client=self)
            guild.voice_states[vs.user_id.id] = vs
        else:
            if data.get('channel_id') is None:
                # disconnect -> remove
                guild.voice_states.pop(usr_id, None)
            else:
                # update existing
                guild.voice_states[usr_id].from_data(**data)

    async def _on_guild_role_update(self, data: dict):
        guild = self.get_guild(int(data['guild_id']))
        role = guild.get_role(int(data['role']['id']))
        # old_role = deepcopy(role)
        role.copy(**data['role'])
        # for event in self._event_listener.get(Event.GUILD_ROLE_UPDATED.value, []):
        #    asyncio.ensure_future(event(old_role, role))

    async def _on_guild_role_delete(self, data: dict):
        guild = self.get_guild(int(data['guild_id']))
        role = guild.get_role(int(data['role_id']))
        guild.roles.pop(int(data['role_id']))
        for event in self._event_listener.get(Event.GUILD_ROLE_DELETED.value, []):
            asyncio.ensure_future(event(role))

    async def _on_guild_role_create(self, data: dict):
        guild = self.get_guild(int(data['guild_id']))
        role = Role(**data['role'], _client=self, _guild=guild)
        guild.roles[role.id] = role
        for event in self._event_listener.get(Event.GUILD_ROLE_CREATED.value, []):
            asyncio.ensure_future(event(role))

    async def _on_guild_update(self, data: dict):
        g = Guild(**data, _client=self)
        old = self.get_guild(g.id)
        self._guilds[g.id].handle_guild_update(**data)
        for event in self._event_listener.get(Event.GUILD_UPDATED.value, []):
            asyncio.ensure_future(event(old, g))

    async def _on_message(self, data: dict):
        # lets check if we know that user
        if self._users.get(int(data.get('author').get('id'))) is None:
            usr = User(**data.get('author'), _client=self)
            self._users[usr.id] = usr
        msg = Message(**data, _client=self)
        # add to cache
        self.messages.append(msg)
        if len(self.messages) > self.message_cache_size:
            self.messages.pop(0)
        # call on_message event
        events = self._event_listener.get(Event.MESSAGE_SEND.value, [])
        for event in events:
            asyncio.ensure_future(event(msg))

    async def _on_guild_member_update(self, data: dict):
        try:
            guild = self.get_guild(int(data.get('guild_id')))
            if guild is None:
                raise Exception('guild member update for unknown guild')
            member = guild.get_member(int(data.get('user').get('id')))
            new_member = Member(**data, _client=self, _guild=guild)
            # lets update the member
            guild._members[new_member.id] = new_member
            if member is not None:
                events = self._event_listener.get(Event.MEMBER_UPDATED.value, [])
                for event in events:
                    asyncio.ensure_future(event(member, new_member))
                pass
            else:
                logging.warning(f'skipped member update for {new_member.id} in {guild.id}: old member not cached')
        except:
            logging.exception('Exception while handling guild member update')
        pass

    async def _on_interaction_create(self, data: dict):
        try:
            interaction = Interaction(**data, _client=self)
            _id = interaction.data.id
            if interaction.type == InteractionType.APPLICATION_COMMAND:
                ac = self._application_commands.get(_id)
                if self.command_listener is not None:
                    asyncio.ensure_future(self.command_listener(ac, interaction))
                if ac is None:
                    logging.error(f'could not find callback for command {interaction.data.name} ({_id})')
                    return
                await ac.callback(interaction)
            elif interaction.type == InteractionType.MESSAGE_COMPONENT:
                if self.interaction_listener is not None:
                    asyncio.ensure_future(self.interaction_listener(interaction))
                ac = self._interaction_handler.get(interaction.data.custom_id)
                if ac is None:
                    logging.exception(f'could not find handler for interaction with custom id {interaction.data.custom_id}')
                    return
                await ac(interaction)
        except:
            logging.exception('Exception while handling interaction:')

    async def _on_ready(self, data: dict):
        for g in data.get('guilds', []):
            self._guilds[int(g['id'])] = None
        # register global commands
        globals_to_override = []
        for c in self._command_registrar:
            if not c.get('global'):
                continue
            globals_to_override.append(c.get('ap').get_json_data())
        _data = await self.http.request(Route('PUT',
                                              f'/applications/{self.application.id}/commands'),
                                        json=globals_to_override)
        for d in _data:
            callback = None
            ap = ApplicationCommand(**d, _client=self)
            for c in self._command_registrar:
                if not c.get('global'):
                    continue
                if c.get('ap').name == ap.name and c.get('ap').type == ap.type:
                    callback = c.get('callback')
                    break
            ap.callback = callback
            self._application_commands[ap.id] = ap
        # call ready event
        # for g in data.get('guilds', []):
        #     await self._register_guild_commands(int(g['id']))
        for event in self._event_listener.get(Event.READY.value, []):
            await event()

    async def _on_member_join(self, data: dict):
        gid = int(data.get('guild_id'))
        guild = self.get_guild(gid)
        member = Member(**data, _client=self, _guild=guild)
        guild._members[member.id] = member
        self.add_user_to_cache(data.get('user'))
        for event in self._event_listener.get(Event.MEMBER_JOINED.value, []):
            await event(member)

    async def _on_guild_create(self, data: dict):
        g = Guild(**data, _client=self)
        if g.id not in self._guilds.keys():
            # new guild!
            for event in self._event_listener.get(Event.GUILD_JOINED.value, []):
                await event(g)
        self._guilds[g.id] = g
        # register server specific commands on join
        await self._register_guild_commands(g.id)

    async def _register_guild_commands(self, gid: int):
        for c in self._command_registrar:
            if c.get('global'):
                continue
            gf = c.get('guild_filter')
            if gf is None or \
                    (isinstance(gf, int) and gf == gid) or \
                    (isinstance(gf, list) and gid in gf):
                ap = c.get('ap')
                data = await self.http.request(Route('POST',
                                                     f'/applications/{self.application.id}/guilds/{gid}/commands',
                                                     guild_id=gid),
                                               json=ap.get_json_data())
                ap = ApplicationCommand(**data, _callback=c.get('callback'), _client=self)
                self._application_commands[ap.id] = ap

    async def _on_guild_delete(self, data: dict):
        if data.get('unavailable') is None:
            # we left the guild
            g = self.get_guild(int(data.get('id')))
            for event in self._event_listener.get(Event.GUILD_LEFT.value, []):
                await event(g)
            # remove from cache
            self._guilds.pop(int(data.get('id')))

########################################################################################################################
#
########################################################################################################################

    async def dispatch_gateway_event(self, event: str, data: dict):
        try:
            if self.gateway_listener is not None:
                asyncio.ensure_future(self.gateway_listener(event, data))
            events = self._raw_gateway_listener.get(event)
            if events is None:
                return
            for event in events:
                await event(data)
        except:
            logging.exception('gateway event handling failed')

    def register_raw_gateway_event_listener(self, event_name: str, listener: Callable[[dict], Awaitable[None]]):
        if event_name not in self._raw_gateway_listener.keys():
            self._raw_gateway_listener[event_name] = []
        self._raw_gateway_listener[event_name].append(listener)

    async def connect(self):
        """establish web socket connection and let websocket listen for stuff"""
        self.ws = DiscordWebSocket(self)
        resume = False
        while not self.is_closed():
            try:
                await self.ws.run(resume=resume)
            except ReconnectWebSocket:
                logging.info(f'Trying to resume session...')
                resume = True
            except (ConnectionClosed,
                    OSError,
                    aiohttp.ClientError,
                    asyncio.TimeoutError):
                if self.is_closed():
                    return
            except asyncio.exceptions.CancelledError:
                await self.close()
            except:
                logging.exception('unhandled exception, lets try a reconnect')
                await self.close()

    async def start(self, token: str):
        await self.login(token)
        await self.fetch_bot_application_information()
        await self.connect()

    async def close(self):
        if self._closed:
            return
        self._closed = True
        await self.http.close()
        await self.ws.close()

    def run(self, token: str, intents: Intents = Intents.default()):
        self._closed = False
        self.intents = intents
        loop = self.loop
        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass

        async def runner():

            try:
                await self.start(token)
            finally:
                if not self.is_closed():
                    print('1')
                    await self.close()

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=self.loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logging.info('shutting down due to keyboard interrupt.')
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            print('cleanup loop')
            _cleanup_loop(self.loop)
        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                return None

########################################################################################################################
# Decorator
########################################################################################################################

    def event(self, name: Union[str, Event]):
        def decorator(func):
            n = name.value if isinstance(name, Event) else name
            if self._event_listener.get(n) is None:
                self._event_listener[n] = []
            self._event_listener[n].append(func)
            return func

        return decorator

    def raw_event(self, name: str):
        def decorator(func):
            self.register_raw_gateway_event_listener(name, func)
            return func
        return decorator

    def interaction_handler(self,
                            custom_id: Optional[str] = None):
        def decorator(func):
            self._interaction_handler[custom_id] = func
            return func
        return decorator

########################################################################################################################
# Fetcher
########################################################################################################################

    async def fetch_user(self, uid: Snowflake) -> User:
        data = await self.http.request(Route('GET', f'/users/{uid.id}'))
        user = User(**data, _client=self)
        self.add_user_to_cache(user)
        return user

    def get_guild(self, s: Union[Snowflake, int]) -> Optional[Guild]:
        return self._guilds.get(s.id if isinstance(s, Snowflake) else s)

    def get_user(self, s: Union[Snowflake, int]) -> Optional[User]:
        return self._users.get(s.id if isinstance(s, Snowflake) else s)

    def get_application_commands(self, name: str, _type: ApplicationCommandType) -> Optional[ApplicationCommand]:
        for ac in self._application_commands.values():
            if ac.type == _type and ac.name == name:
                return ac
        return None

    def add_user_to_cache(self, user: Union[User, dict]):
        """Adds a user to the local cache."""
        if isinstance(user, dict):
            user = User(**user, _client=self)
        if self._users.get(user.id) is None:
            self._users[user.id] = user

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

########################################################################################################################
# Command registration
########################################################################################################################

    def register_command(self,
                         ap: ApplicationCommand,
                         callback,
                         is_global: bool,
                         guild_filter: Union[int, None, List[int]]):
        if is_global:
            # register global command
            self._command_registrar.append({
                'ap': ap,
                'callback': callback,
                'global': True
            })
        else:
            # register internally for server specific
            self._command_registrar.append({
                'ap': ap,
                'global': False,
                'guild_filter': guild_filter,
                'callback': callback
            })
