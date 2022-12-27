import asyncio
import json
import typing
from typing import Optional, Iterable, Dict, Any, List, Union

import aiohttp
from aiohttp import ClientSession, ClientResponse
from . import utils
from .errors import HTTPException, GatewayNotFound, Forbidden, NotFound, DiscordServerError
import logging
from .message import Message
from .route import Route
from .channel import get_channel

if typing.TYPE_CHECKING:
    from .file import File
    from .base_client import BaseClient
    from .components import BaseComponent
    from .channel import Thread


async def get_json_or_str(response: ClientResponse):
    text = await response.text(encoding='utf-8')
    ct = response.headers.get('content-type')
    if ct is not None and ct == 'application/json':
        return json.loads(text)
    return text


class MaybeUnlock:

    def __init__(self, lock):
        self.lock = lock
        self._unlock = True

    def __enter__(self):
        return self

    def defer(self):
        self._unlock = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._unlock:
            self.lock.release()


class HTTPClient:

    request_listener = None

    def __init__(self, client: 'BaseClient', loop=None):
        self.client: 'BaseClient' = client
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.user_agent = 'DiscordBot (https://github.com/Teekeks/DisTee.py v{version})'.format(version=utils.VERSION)
        self.__session: Optional[ClientSession] = None
        self.token: Optional[str] = None
        self._locks = {}
        self._global_lock_over = asyncio.Event()
        self._global_lock_over.set()

    async def close(self):
        if self.__session:
            await self.__session.close()

    async def do_login(self, token: str):
        self.__session = ClientSession()
        self.token = token
        try:
            data = await self.request(Route('GET', '/users/@me'))
        except HTTPException:
            logging.exception('Exception on login')
            return None
        return data
    pass

    async def get_gateway(self, resume: bool, resume_gateway: str = None, encoding: str = 'json', zlib: bool = True) -> str:
        if resume and resume_gateway is not None:
            url = resume_gateway
        else:
            try:
                data = await self.request(Route('GET', '/gateway'))
                url = data['url']
            except HTTPException as ex:
                raise GatewayNotFound from ex
        if zlib:
            return f'{url}?encoding={encoding}&v={utils.GATEWAY_VERSION}&compress=zlib-stream'
        else:
            return f'{url}?encoding={encoding}&v={utils.GATEWAY_VERSION}'

    async def ws_connect(self, url: str):
        return await self.__session.ws_connect(url, timeout=30)

    async def edit_message(self,
                           route: Route,
                           *,
                           files: List['File'] = None,
                           content: Optional[str] = None,
                           tts: bool = False,
                           embeds: Optional[Dict] = None,
                           nonce: Optional[str] = None,
                           allowed_mentions: Optional[Dict] = None,
                           message_reference: Optional[Dict] = None,
                           stickers: Optional[List] = None,
                           components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                           flags: Optional[int] = None) -> 'Message':
        payload = {'tts': tts}
        form = []
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
        form.append({'name': 'payload_json', 'value': json.dumps(payload)})
        data = await self.request(route, form=form)
        return Message(**data, _client=self.client)
    pass

    async def send_message(self,
                           route: Route,
                           *,
                           files: List['File'] = None,
                           content: Optional[str] = None,
                           tts: bool = False,
                           embeds: Optional[Dict] = None,
                           nonce: Optional[str] = None,
                           allowed_mentions: Optional[Dict] = None,
                           message_reference: Optional[Dict] = None,
                           stickers: Optional[List] = None,
                           components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                           flags: Optional[int] = None) -> 'Message':
        if files is not None:
            return await self.send_multipart(route,
                                             files=files,
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
        d = await self.request(route, form=form)
        return Message(**d, _client=self.client)

    async def send_multipart(self,
                             route: Route,
                             *,
                             files: List['File'] = None,
                             content: Optional[str] = None,
                             tts: bool = False,
                             embeds: Optional[Dict] = None,
                             nonce: Optional[str] = None,
                             allowed_mentions: Optional[Dict] = None,
                             message_reference: Optional[Dict] = None,
                             stickers: Optional[List] = None,
                             components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                             flags: Optional[int] = None) -> 'Message':
        payload = {'tts': tts}
        form = []
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
        d = await self.request(route, form=form, files=files)
        return Message(**d, _client=self.client)

    async def create_thread(self,
                            route: Route,
                            *,
                            name: str,
                            auto_archive_duration: Optional[int] = None,
                            rate_limit_per_user: Optional[int] = None,
                            applied_tags: Optional[List[int]] = None,
                            files: List['File'] = None,
                            content: Optional[str] = None,
                            embeds: Optional[Dict] = None,
                            nonce: Optional[str] = None,
                            allowed_mentions: Optional[Dict] = None,
                            message_reference: Optional[Dict] = None,
                            stickers: Optional[List] = None,
                            components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                            flags: Optional[int] = None) -> ('Thread', 'Message'):
        if files is not None:
            return await self.create_thread_multipart(route,
                                                      name=name,
                                                      auto_archive_duration=auto_archive_duration,
                                                      rate_limit_per_user=rate_limit_per_user,
                                                      applied_tags=applied_tags,
                                                      files=files,
                                                      content=content,
                                                      embeds=embeds,
                                                      nonce=nonce,
                                                      allowed_mentions=allowed_mentions,
                                                      message_reference=message_reference,
                                                      stickers=stickers,
                                                      components=components,
                                                      flags=flags)

        message_payload = {}
        if content is not None:
            message_payload['content'] = content
        if message_reference is not None:
            message_payload['message_reference'] = message_reference
        if embeds is not None:
            message_payload['embeds'] = embeds
        if components is not None:
            message_payload['components'] = utils.get_components(components)
        if allowed_mentions is not None:
            message_payload['allowed_mentions'] = allowed_mentions
        if nonce is not None:
            message_payload['nonce'] = nonce
        if stickers is not None:
            message_payload['sticker_ids'] = stickers
        if flags is not None:
            message_payload['flags'] = flags
        payload = {
            'name': name,
            'message': message_payload
        }
        if auto_archive_duration is not None:
            payload['auto_archive_duration'] = auto_archive_duration
        if rate_limit_per_user is not None:
            payload['rate_limit_per_user'] = rate_limit_per_user
        if applied_tags is not None:
            payload['applied_tags'] = applied_tags
        d = await self.request(route, json=payload)
        thread = get_channel(**d, _client=self.client)
        message = Message(**d['message'], _client=self.client)
        return thread, message

    async def create_thread_multipart(self,
                                      route: Route,
                                      *,
                                      name: str,
                                      auto_archive_duration: Optional[int] = None,
                                      rate_limit_per_user: Optional[int] = None,
                                      applied_tags: Optional[List[int]] = None,
                                      files: List['File'] = None,
                                      content: Optional[str] = None,
                                      embeds: Optional[Dict] = None,
                                      nonce: Optional[str] = None,
                                      allowed_mentions: Optional[Dict] = None,
                                      message_reference: Optional[Dict] = None,
                                      stickers: Optional[List] = None,
                                      components: Optional[List[Union[dict, 'BaseComponent']]] = None,
                                      flags: Optional[int] = None) -> 'Thread':
        payload = {}
        form = []
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
        d = await self.request(route, form=form, files=files)
        return get_channel(**d, _client=self.client)

    async def request(self,
                      route: Route,
                      form: Optional[Iterable[Dict[str, Any]]] = None,
                      files: Optional[Iterable['File']] = None,
                      **kwargs):
        if self.request_listener is not None:
            asyncio.ensure_future(self.request_listener(route))
        method = route.method
        bucket = route.bucket
        url = route.url

        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[bucket] = lock

        headers = {
            'User-Agent': self.user_agent,
            'X-RateLimit-Precision': 'millisecond',
            'Authorization': f'Bot {self.token}'
        }

        if kwargs.get('reason'):
            headers['X-Audit-Log-Reason'] = kwargs.pop('reason')
        kwargs.pop('reason', None)

        kwargs['headers'] = headers

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json'))

        # wait for a global api lock to be over :(
        if not self._global_lock_over.is_set():
            await self._global_lock_over.wait()

        await lock.acquire()
        with MaybeUnlock(lock) as maybe_unlock:
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

                    async with self.__session.request(method=method, url=url, **kwargs) as r:
                        logging.debug(f'{method} {url} with {str(kwargs.get("data"))} has returned {r.status}')
                        data = await get_json_or_str(r)

                        remaining = r.headers.get('X-Ratelimit-Remaining')

                        if remaining == '0' and r.status != 429:
                            # bucket depleted :(
                            delta = float(r.headers.get('X-Ratelimit-Reset-After'))
                            logging.debug(f'A rate limit bucket has been exhausted (bucket: {bucket}, retry: {delta})')
                            maybe_unlock.defer()
                            self.loop.call_later(delta, lock.release)

                        if 300 > r.status >= 200:
                            return data

                        if r.status == 429:
                            if not r.headers.get('Via'):
                                # this is cloudflare :(
                                raise HTTPException(r, data)

                            retry_after = float(data['retry_after'])
                            logging.warning(f'We are being rate limited. Retrying in {retry_after:.2f} seconds. Bucket: {bucket}')
                            is_global = data.get('global', False)
                            if is_global:
                                logging.warning(f'Global rate limit has been hit. Retrying in {retry_after:.2f} seconds.')
                                self._global_lock_over.clear()
                            await asyncio.sleep(retry_after)
                            logging.debug(f'Done waiting for rate limit, retrying now...')
                            if is_global:
                                self._global_lock_over.set()
                                logging.debug('Global rate limit is over!')
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
