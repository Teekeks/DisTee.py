import asyncio
import json
from typing import Optional, Iterable, Dict, Any
from .utils import Snowflake
import aiohttp
from aiohttp import ClientSession, ClientResponse
from . import utils
from .errors import HTTPException, GatewayNotFound, Forbidden, NotFound, DiscordServerError
import logging
from pprint import pprint


async def get_json_or_str(response: ClientResponse):
    text = await response.text(encoding='utf-8')
    ct = response.headers.get('content-type')
    if ct is not None and ct == 'application/json':
        return json.loads(text)
    return text


class Route:
    BASE_URL = f'https://discord.com/api/v{utils.API_VERSION}'

    def __init__(self, method: str, path: str, **parameters):
        self.path = path
        self.method = method
        self.url = self.BASE_URL + self.path

        if parameters:
            for k, v in parameters.items():
                self.url = self.url.replace('{'+k+'}', str(v.id) if isinstance(v, Snowflake) else str(v))

        self.channel_id = parameters.get('channel_id')
        if isinstance(self.channel_id, Snowflake):
            self.channel_id = self.channel_id.id
        self.guild_id = parameters.get('guild_id')
        if isinstance(self.guild_id, Snowflake):
            self.guild_id = self.guild_id.id

    @property
    def bucket(self):
        return f'{self.channel_id}:{self.guild_id}:{self.path}'


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

    def __init__(self, loop=None):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.user_agent = 'DisTee v{version}'.format(version=utils.VERSION)
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

    async def get_gateway(self, encoding: str = 'json', zlib: bool = True) -> str:
        try:
            data = await self.request(Route('GET', '/gateway'))
        except HTTPException as ex:
            raise GatewayNotFound from ex
        if zlib:
            return f'{data["url"]}?encoding={encoding}&v={utils.GATEWAY_VERSION}&compress=zlib-stream'
        else:
            return f'{data["url"]}?encoding={encoding}&v={utils.GATEWAY_VERSION}'

    async def ws_connect(self, url: str):
        return await self.__session.ws_connect(url, timeout=30)

    async def request(self,
                      route: Route,
                      form: Optional[Iterable[Dict[str, Any]]] = None,
                      **kwargs):
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

        kwargs['headers'] = headers

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json'))

        if form is not None:
            form_data = aiohttp.FormData()
            for p in form:
                form_data.add_field(**p)
            kwargs['data'] = form_data

        # wait for a global api lock to be over :(
        if not self._global_lock_over.is_set():
            await self._global_lock_over.wait()

        await lock.acquire()
        with MaybeUnlock(lock) as maybe_unlock:
            for tries in range(5):
                try:
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

                            retry_after = float(data['retry_after']) / 1000.0
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
