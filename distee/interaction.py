from .utils import Snowflake, snowflake_or_none
from .enums import InteractionType, ApplicationCommandType, InteractionResponseType, ComponentType
from .flags import InteractionCallbackFlags
from typing import Optional, List
from .guild import Member
from .user import User
from .message import Message
from .channel import BaseChannel, get_channel


class InteractionResponse:

    def __init__(self):
        self.type: InteractionResponseType = InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE
        self.tts: Optional[bool] = None
        self.content: Optional[str] = None
        self.embeds: Optional[List[dict]] = None
        self.allowed_mentions: Optional[dict] = None
        self.flags: Optional[InteractionCallbackFlags] = None
        self.components = None

    def get_json_data(self):
        return {
            'type': self.type.value,
            'data': {k: v for k, v in {
                'content': self.content,
                'flags': self.flags,
                'tts': self.tts,
                'components': self.components,
                'embeds': self.embeds
            }.items() if v is not None}
        }

    @property
    def ephemeral(self) -> bool:
        return False

    @ephemeral.setter
    def ephemeral(self, val: bool):
        if val:
            if self.flags is None:
                self.flags = 0
            self.flags += InteractionCallbackFlags.EPHEMERAL
        else:
            self.flags -= InteractionCallbackFlags.EPHEMERAL


class InteractionData(Snowflake):

    def __init__(self, **data):
        super(InteractionData, self).__init__(**data)
        self.name: str = data.get('name')
        self.type: ApplicationCommandType = ApplicationCommandType(data.get('type')) \
            if data.get('type') is not None else None
        self.component_type: ComponentType = ComponentType(data.get('component_type')) \
            if data.get('component_type') is not None else None
        self.custom_id: Optional[str] = data.get('custom_id')
        self.values: Optional[List] = data.get('values')
        res = data.get('resolved')
        self.messages: List[Message] = [Message(**d, _client=self._client) for d in
                                        res.get('messages').values()] \
            if res is not None and res.get('messages') is not None else []
        self.users: List[User] = [User(**d, _client=self._client) for d in
                                  res.get('users').values()] \
            if res is not None and res.get('users') is not None else []
        self.channels: List[BaseChannel] = [get_channel(**d, _client=self._client) for d in
                                            res.get('channels').values()] \
            if res is not None and res.get('channels') is not None else []

        self.target_id: Optional[Snowflake] = snowflake_or_none(data.get('target_id'))
        # FIXME implement missing things https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-object-interaction-data-structure


class Interaction(Snowflake):
    
    def __init__(self, **data):
        super(Interaction, self).__init__(**data)
        self.application_id: Optional[Snowflake] = Snowflake(id=data.get('application_id'))
        self.type: InteractionType = InteractionType(data.get('type'))
        self.guild_id: Optional[Snowflake] = snowflake_or_none(data.get('guild_id'))
        self.channel_id: Optional[Snowflake] = snowflake_or_none(data.get('channel_id'))
        self.member: Optional[Member] = Member(**data.get('member'), _client=self._client) \
            if data.get('member') is not None else None
        self.user: Optional[User] = User(**data.get('user'), _client=self._client) \
            if data.get('user') is not None else None
        self.token: str = data.get('token')
        self.version: int = data.get('version')
        self.data: Optional[InteractionData] = InteractionData(**data.get('data'), _client=self._client) \
            if data.get('data') is not None else None
        self.response: InteractionResponse = InteractionResponse()
