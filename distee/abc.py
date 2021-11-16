from typing import Optional, List
import json
from distee.channel import GuildChannel, MessageableChannel
from distee.http import Route


class Messageable:

    def _get_reference(self, msg: 'Message') -> dict:
        return {
            'message_id': msg.id,
            'channel_id': msg.channel_id.id
        }

    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    async def send(self,
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
        gid = None
        if isinstance(self, GuildChannel):
            gid = self.guild_id
        await self._client.http.request(Route('POST',
                                              f'/channels/{channel.id}/messages',
                                              channel_id=self.id,
                                              guild_id=gid),
                                        form=form)
