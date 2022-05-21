import typing

from .attachment import Attachment
from .components import Modal
from .errors import WrongInteractionTypeException
from .route import Route
from .utils import Snowflake, snowflake_or_none, get_json_from_dict, get_components
from .enums import InteractionType, ApplicationCommandType, InteractionResponseType, ComponentType
from .flags import InteractionCallbackFlags
from typing import Optional, List, Dict, Union
from .guild import Member, Guild
from .user import User
from .message import Message
from .channel import BaseChannel, get_channel

if typing.TYPE_CHECKING:
    from .file import File
    from .components import BaseComponent


def get_parsed_modal_components(data) -> Optional[dict]:
    d = {}
    if data is None:
        return None
    for line in data:
        for comp in line.get('components', []):
            d[comp['custom_id']] = comp
    return d


class InteractionData(Snowflake):

    def __init__(self, **data):
        super(InteractionData, self).__init__(**data)
        self._interaction: 'Interaction' = data.get('_interaction')
        self.name: str = data.get('name')
        self.type: ApplicationCommandType = ApplicationCommandType(data.get('type')) \
            if data.get('type') is not None else None
        self.component_type: ComponentType = ComponentType(data.get('component_type')) \
            if data.get('component_type') is not None else None
        self.custom_id: Optional[str] = data.get('custom_id')
        self.values: Optional[List] = data.get('values')
        self.options: Optional[List] = data.get('options')
        res = data.get('resolved')
        self.members: Dict[int, Member] = {int(d['user']['id']): Member(**d, _client=self._client, _guild=self._interaction.guild) for d in
                                           res.get('members').values()}
        self.messages: Dict[int, Message] = {int(d['id']): Message(**d, _client=self._client) for d in
                                             res.get('messages').values()} \
            if res is not None and res.get('messages') is not None else {}
        self.users: Dict[int, User] = {int(d['id']): User(**d, _client=self._client) for d in
                                       res.get('users').values()} \
            if res is not None and res.get('users') is not None else {}
        self.attachments: Dict[int, Attachment] = {int(d['id']): Attachment(**d, _client=self._client) for d in
                                                   res.get('attachments').values()} \
            if res is not None and res.get('attachments') is not None else {}
        self.channels: Dict[int, BaseChannel] = {int(d['id']): get_channel(**d, _client=self._client) for d in
                                                 res.get('channels').values()} \
            if res is not None and res.get('channels') is not None else {}

        self.target_id: Optional[Snowflake] = snowflake_or_none(data.get('target_id'))
        self.components: Optional[Dict] = get_parsed_modal_components(data.get('components'))
        # FIXME implement missing things https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-object-interaction-data-structure


class Interaction(Snowflake):
    
    def __init__(self, **data):
        super(Interaction, self).__init__(**data)
        self.application_id: Optional[Snowflake] = Snowflake(id=data.get('application_id'))
        self.type: InteractionType = InteractionType(data.get('type'))
        self.guild_id: Optional[Snowflake] = snowflake_or_none(data.get('guild_id'))
        self.guild: Optional[Guild] = self._client.get_guild(self.guild_id) if self.guild_id is not None else None
        self.channel_id: Optional[Snowflake] = snowflake_or_none(data.get('channel_id'))
        self.member: Optional[Member] = Member(**data.get('member'),
                                               _client=self._client,
                                               _guild=self._client.get_guild(self.guild_id)) \
            if data.get('member') is not None else None
        self.user: Optional[User] = User(**data.get('user'), _client=self._client) \
            if data.get('user') is not None else None
        self.token: str = data.get('token')
        self.version: int = data.get('version')
        self.data: Optional[InteractionData] = InteractionData(**data.get('data'), _client=self._client, _interaction=self) \
            if data.get('data') is not None else None
        self.message: Optional[Message] = Message(**data.get('message'), _client=self._client) \
            if data.get('message') is not None else None
        self.locale: Optional[str] = data.get('locale')
        self.guild_locale: Optional[str] = data.get('guild_locale')

    async def defer_update_message(self):
        """ACK component interaction now and edit message later"""
        if self.type != InteractionType.MESSAGE_COMPONENT:
            raise WrongInteractionTypeException()
        await self._client.http.request(Route('POST',
                                              '/interactions/{interaction_id}/{interaction_token}/callback',
                                              interaction_id=self.id,
                                              interaction_token=self.token),
                                        json={'type': InteractionResponseType.DEFERRED_UPDATE_MESSAGE.value, 'data': {}})

    async def update_message(self,
                             content: Optional[str] = None,
                             tts: Optional[bool] = None,
                             embeds: Optional[List[dict]] = None,
                             allowed_mentions: Optional[dict] = None,
                             components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                             ephemeral: Optional[bool] = None):
        """ACK interaction and edit component message"""
        if self.type != InteractionType.MESSAGE_COMPONENT:
            raise WrongInteractionTypeException()
        json = {'type': InteractionResponseType.UPDATE_MESSAGE.value,
                'data': {k: v for k, v in {
                        'content': content,
                        'flags': 1 << 6 if ephemeral else None,
                        'tts': tts,
                        'components': get_components(components),
                        'embeds': embeds,
                        'allowed_mentions': allowed_mentions
                    }.items() if v is not None}}
        await self._client.http.request(Route('POST',
                                              '/interactions/{interaction_id}/{interaction_token}/callback',
                                              interaction_id=self.id,
                                              interaction_token=self.token),
                                        json=json)

    async def send(self,
                   content: Optional[str] = None,
                   embeds: Optional[List[dict]] = None,
                   tts: Optional[bool] = None,
                   allowed_mentions: Optional[dict] = None,
                   components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                   stickers: Optional[List] = None,
                   nonce: Optional[str] = None,
                   ephemeral: Optional[bool] = None):
        """ACK interaction and send a message as response"""
        json = {'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE.value,
                'data': {k: v for k, v in {
                        'content': content,
                        'flags': 1 << 6 if ephemeral else None,
                        'tts': tts,
                        'components': get_components(components),
                        'embeds': embeds,
                        'sticker_ids': stickers,
                        'nonce': nonce,
                        'allowed_mentions': allowed_mentions
                    }.items() if v is not None}}
        await self._client.http.request(Route('POST',
                                              '/interactions/{interaction_id}/{interaction_token}/callback',
                                              interaction_id=self.id,
                                              interaction_token=self.token),
                                        json=json)

    async def send_followup(self,
                            content: str = None,
                            tts: bool = False,
                            embeds: Optional[List[dict]] = None,
                            components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                            allowed_mentions: Optional[dict] = None,
                            stickers: Optional[List] = None,
                            nonce: Optional[str] = None,
                            files: Optional['File'] = None,
                            ephemeral: Optional[bool] = None):
        """send a followup message after deferring it"""
        return await self._client.http.send_message(Route('POST',
                                                          '/webhooks/{application_id}/{interaction_token}',
                                                          application_id=self.application_id,
                                                          interaction_token=self.token),
                                                    components=get_components(components),
                                                    content=content,
                                                    tts=tts,
                                                    embeds=embeds,
                                                    allowed_mentions=allowed_mentions,
                                                    flags=1 << 6 if ephemeral else None,
                                                    stickers=stickers,
                                                    nonce=nonce,
                                                    files=files)

    async def defer_send(self, ephemeral: Optional[bool] = None):
        """ACK now and use send later"""
        json = {'type': InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE.value,
                'data': {'flags': 1 << 6} if ephemeral else {}}
        await self._client.http.request(Route('POST',
                                              '/interactions/{interaction_id}/{interaction_token}/callback',
                                              interaction_id=self.id,
                                              interaction_token=self.token),
                                        json=json)

    async def send_modal(self, data: Union[Dict, Modal]):
        json = {'type': InteractionResponseType.MODAL.value,
                'data': data if isinstance(data, dict) else data.to_json()}
        await self._client.http.request(Route('POST',
                                              '/interactions/{interaction_id}/{interaction_token}/callback',
                                              interaction_id=self.id,
                                              interaction_token=self.token),
                                        form=[{'name': 'payload_json', 'value': get_json_from_dict(json)}])
