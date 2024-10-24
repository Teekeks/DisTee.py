from typing import List, Optional, Dict, Union, TYPE_CHECKING, Iterable, Any
import json
from . import utils
import logging
import aiohttp
from .http import get_json_or_str
from .errors import HTTPException, Forbidden, NotFound, DiscordServerError
import asyncio
from .message import Message
if TYPE_CHECKING:
    from .file import File
    from .base_client import BaseClient
    from .components import BaseComponent


class Webhook:

    def __init__(self, client: 'BaseClient', url: str, default_username: str = None):
        self.default_username = default_username
        self.client = client
        self.url = url

    async def send_message(self,
                           *,
                           content: Optional[str] = None,
                           username: Optional[str] = None,
                           files: List['File'] = None,
                           tts: bool = False,
                           embeds: Optional[Dict] = None,
                           nonce: Optional[str] = None,
                           allowed_mentions: Optional[Dict] = None,
                           message_reference: Optional[Dict] = None,
                           stickers: Optional[List] = None,
                           components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                           flags: Optional[int] = None) -> Optional['Message']:
        if files is not None:
            return await self.send_multipart(files=files,
                                             content=content,
                                             tts=tts,
                                             embeds=embeds,
                                             nonce=nonce,
                                             allowed_mentions=allowed_mentions,
                                             message_reference=message_reference,
                                             stickers=stickers,
                                             components=components,
                                             flags=flags)

        payload = {'tts': tts}
        form = []
        if self.default_username is not None:
            payload['username'] = self.default_username
        if username is not None:
            payload['username'] = username
        if content is not None:
            payload['content'] = content
        if message_reference is not None:
            payload['message_reference'] = message_reference
        if embeds is not None:
            payload['embeds'] = embeds
        if components is not None:
            payload['components'] = utils.get_components(components)
        if allowed_mentions is not None:
            payload['allowed_mentions'] = allowed_mentions
        if nonce is not None:
            payload['nonce'] = nonce
        if stickers is not None:
            payload['sticker_ids'] = stickers
        if flags is not None:
            payload['flags'] = flags
        form.append({'name': 'payload_json', 'value': json.dumps(payload)})
        d = await self.request(form=form)
        if isinstance(d, str):
            return None
        return Message(**d, _client=self.client)

    async def send_multipart(self,
                             content: Optional[str] = None,
                             username: Optional[str] = None,
                             files: List['File'] = None,
                             tts: bool = False,
                             embeds: Optional[Dict] = None,
                             nonce: Optional[str] = None,
                             allowed_mentions: Optional[Dict] = None,
                             message_reference: Optional[Dict] = None,
                             stickers: Optional[List] = None,
                             components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                             flags: Optional[int] = None) -> Optional['Message']:
        payload = {'tts': tts}
        form = []
        if content is not None:
            payload['content'] = content
        if self.default_username is not None:
            payload['username'] = self.default_username
        if username is not None:
            payload['username'] = username
        if message_reference is not None:
            payload['message_reference'] = message_reference
        if embeds is not None:
            payload['embeds'] = embeds
        if components is not None:
            payload['components'] = utils.get_components(components)
        if allowed_mentions is not None:
            payload['allowed_mentions'] = allowed_mentions
        if nonce is not None:
            payload['nonce'] = nonce
        if stickers is not None:
            payload['sticker_ids'] = stickers
        if flags is not None:
            payload['flags'] = flags
        if files is not None:
            if len(files) == 1:
                payload['attachments'] = [{
                    'id': 0,
                    'description': files[0].description
                }]
        form.append({'name': 'payload_json', 'value': json.dumps(payload)})
        if len(files) == 1:
            file = files[0]
            form.append({
                'name': 'files[0]',
                'value': file.fp,
                'filename': file.filename,
                'content_type': 'application/octet-stream',
                'content_transfer_encoding': 'binary'
            })
        d = await self.request(form=form, files=files)
        if isinstance(d, str):
            return None
        return Message(**d, _client=self.client)

    async def request(self,
                      form: Optional[Iterable[Dict[str, Any]]] = None,
                      files: Optional[Iterable['File']] = None,
                      **kwargs):
        # if self.request_listener is not None:
        #     asyncio.ensure_future(self.request_listener(route))
        url = self.url

        headers = {
            'User-Agent': self.client.http.user_agent,
            'X-RateLimit-Precision': 'millisecond',
        }

        if kwargs.get('reason'):
            headers['X-Audit-Log-Reason'] = kwargs.pop('reason')
        kwargs.pop('reason', None)

        kwargs['headers'] = headers

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json'))


        for tries in range(5):
            try:
                if files is not None:
                    for f in files:
                        f.reset(seek=tries)

                if form is not None:
                    form_data = aiohttp.FormData(quote_fields=False)
                    for p in form:
                        form_data.add_field(**p)
                    kwargs['data'] = form_data

                async with aiohttp.request(method='POST', url=url, **kwargs) as r:
                    logging.debug(f'Webhook execution {url} with {str(kwargs.get("data"))} has returned {r.status}')
                    data = await get_json_or_str(r)

                    remaining = r.headers.get('X-Ratelimit-Remaining')

                    if remaining == '0' and r.status != 429:
                        # bucket depleted :(
                        delta = float(r.headers.get('X-Ratelimit-Reset-After'))
                        logging.debug(f'A rate limit bucket has been exhausted (retry: {delta})')
                        await asyncio.sleep(delta)

                    if 300 > r.status >= 200:
                        return data

                    if r.status == 429:
                        if not r.headers.get('Via'):
                            # this is cloudflare :(
                            raise HTTPException(r, data)

                        retry_after = float(data['retry_after'])
                        logging.warning(f'Webhook is being rate limited. Retrying in {retry_after:.2f} seconds.')
                        is_global = data.get('global', False)
                        if is_global:
                            logging.warning(f'Global rate limit has been hit. Retrying in {retry_after:.2f} seconds.')
                        await asyncio.sleep(retry_after)
                        logging.debug(f'Done waiting for rate limit, retrying now...')
                        continue

                    # server error -> retry
                    if r.status in (500, 502):
                        await asyncio.sleep(1 + tries * 2)
                        continue

                    if r.status == 403:
                        raise Forbidden(r, data)

                    if r.status == 404:
                        raise NotFound(r, data)

                    if r.status == 503:
                        raise DiscordServerError(r, data)
                    else:
                        raise HTTPException(r, data)
            except OSError as e:
                if tries < 4 and e.errno in (54, 10054):
                    continue
                raise

            if r.status >= 500:
                raise DiscordServerError(r, data)
            raise HTTPException(r, data)
