import asyncio
import json
from typing import Optional, Iterable, Dict, Any

import aiohttp
from aiohttp import ClientSession, ClientResponse
from . import utils
from .errors import HTTPException, GatewayNotFound
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


class HTTPClient:

    def __init__(self, loop=None):
        self.loop: asyncio.get_event_loop() if loop is None else loop
        self.user_agent = 'DisTee v{version}'.format(version=utils.VERSION)
        self.__session: Optional[ClientSession] = None
        self.token: Optional[str] = None

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
        url = route.url
        headers = {
            'User-Agent': self.user_agent,
            'X-RateLimit-Precision': 'millisecond',
            'Authorization': f'Bot {self.token}'
        }

        kwargs['headers'] = headers

        if form is not None:
            form_data = aiohttp.FormData()
            for p in form:
                form_data.add_field(**p)
            kwargs['data'] = form_data

        try:
            async with self.__session.request(method=method, url=url, **kwargs) as r:
                logging.debug(f'{method} {url} with {str(kwargs.get("data"))} has returned {r.status}')
                data = await get_json_or_str(r)
                if 300 > r.status >= 200:
                    return data
                logging.error('request failed')
                pprint(data)
        except Exception:
            logging.exception('Request failed with Exception')
        # FIXME propper error handling & retry
        pass
