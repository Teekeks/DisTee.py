import asyncio
import logging

from aiohttp import web
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import json

from distee.base_client import BaseClient


class WebhookClient(BaseClient):
    public_key: str
    token: str
    verify_key = VerifyKey
    app: web.Application = web.Application()

    async def handle_callback(self, request: web.Request):
        # check validity
        signature = request.headers['X-Signature-Ed25519']
        timestamp = request.headers['X-Signature-Timestamp']
        body = (await request.content.read()).decode('utf-8')
        try:
            self.verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        except BadSignatureError:
            return web.Response(body='invalid request signature', status=401)
        # handle PING
        data = json.loads(body)
        if data['type'] == 1:
            return web.json_response({'type': 1})
        else:
            await super()._on_interaction_create(data)

    async def startup(self):
        logging.info('started up!')
        await self.login(self.token)
        await self.fetch_bot_application_information()
        await self._register_global_commands()

    def run(self, public_key: str, port: int, host: str, token: str):
        self.token: str = token
        self.public_key = public_key
        self.verify_key = VerifyKey(bytes.fromhex(public_key))
        self.app.add_routes([web.post('/', self.handle_callback)])
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.startup(), loop=loop)
        web.run_app(self.app, port=port, host=host, loop=loop)

