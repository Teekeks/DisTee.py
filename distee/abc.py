from typing import Optional, List, TYPE_CHECKING, Union
import json
from distee.http import Route
from distee.utils import Snowflake
from distee.message import Message

if TYPE_CHECKING:
    from distee.channel import MessageableChannel
    from .file import File


class Messageable:

    def _get_reference(self, msg: 'Message') -> dict:
        return {
            'message_id': msg.id,
            'channel_id': msg.channel_id.id
        } if msg is not None else None

    async def _get_channel(self) -> 'MessageableChannel':
        raise NotImplementedError

    async def send(self,
                   content: str = None,
                   tts: bool = False,
                   reply_to: 'Message' = None,
                   embeds: Optional[List[dict]] = None,
                   components: Optional[List] = None,
                   allowed_mentions: Optional[dict] = None,
                   stickers: Optional[List] = None,
                   nonce: Optional[str] = None,
                   files: Optional['File'] = None,
                   flags: Optional[int] = None) -> 'Message':
        channel = await self._get_channel()
        return await self._client.http.send_message(Route('POST',
                                                          '/channels/{channel_id}/messages',
                                                          channel_id=channel.id),
                                                    files=files,
                                                    content=content,
                                                    tts=tts,
                                                    embeds=embeds,
                                                    nonce=nonce,
                                                    allowed_mentions=allowed_mentions,
                                                    message_reference=self._get_reference(reply_to),
                                                    stickers=stickers,
                                                    components=components,
                                                    flags=flags)

    async def edit_message(self, msg_id: Optional[Union[int, Snowflake]],
                           content: str = None,
                           tts: bool = False,
                           reply_to: 'Message' = None,
                           embeds: Optional[List[dict]] = None,
                           components: Optional[List] = None,
                           allowed_mentions: Optional[dict] = None) -> 'Message':
        payload = {'tts': tts}
        channel = await self._get_channel()
        form = []
        if content is not None:
            payload['content'] = content
        if reply_to is not None:
            payload['message_reference'] = self._get_reference(reply_to)
        if embeds is not None:
            payload['embeds'] = embeds
        if components is not None:
            payload['components'] = components
        if allowed_mentions is not None:
            payload['allowed_mentions'] = allowed_mentions
        form.append({'name': 'payload_json', 'value': json.dumps(payload)})
        d = await self._client.http.request(Route('PATCH',
                                                  '/channels/{channel_id}/messages{message_id}',
                                                  channel_id=channel.id,
                                                  message_id=msg_id),
                                            form=form)
        return Message(**d, _client=channel._client)
