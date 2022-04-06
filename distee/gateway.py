import asyncio
import json
import logging
import threading
import time
import zlib
from . import utils

import aiohttp
from aiohttp import ClientWebSocketResponse
from concurrent import futures
from .errors import WebSocketClosure, ReconnectWebSocket, ConnectionClosed


class HeartbeatThread(threading.Thread):

    def __init__(self, ws, interval):
        super(HeartbeatThread, self).__init__()
        self.ws: 'DiscordWebSocket' = ws
        self.stop_event = threading.Event()
        self.interval = interval
        self._last_recv = time.perf_counter()
        self.heartbeat_timeout = 60
        self.latency = float('inf')
        self._last_send = time.perf_counter()
        self._last_ack = time.perf_counter()

    def run(self) -> None:
        while not self.stop_event.wait(self.interval):
            f = asyncio.run_coroutine_threadsafe(self.ws.send_heartbeat(), loop=self.ws.loop)
            try:
                # block until sending is complete
                total = 0
                while True:
                    try:
                        f.result(10)
                        break
                    except futures.TimeoutError:
                        total += 10
                        logging.exception('Exception in heartbeat thread')
            except Exception:
                self.stop()
            else:
                self._last_send = time.perf_counter()

    def get_payload(self):
        return {
            'op': self.ws.HEARTBEAT,
            'd': self.ws.sequence
        }

    def tick(self):
        self._last_recv = time.perf_counter()

    def ack(self):
        ack_time = time.perf_counter()
        self._last_ack = ack_time
        self.latency = ack_time - self._last_send
        if self.latency > 10:
            logging.warning(f'Can\'t keep up, gateway is {self.latency:.2f}s behind')
        pass

    def stop(self):
        self.stop_event.set()


class GatewayRateLimiter:

    def __init__(self):
        self.lock: asyncio.Lock = asyncio.Lock()
        self.remaining = 110
        self.max = 110
        self.window = 0.0
        self.per = 60.0

    def get_delay(self):
        current = time.time()
        if current > self.window + self.per:
            self.remaining = self.max
        if self.remaining == self.max:
            self.window = current
        if self.remaining == 0:
            return self.per - (current - self.window)
        self.remaining -= 1
        return 0.0

    async def block(self):
        async with self.lock:
            delta = self.get_delay()
            if delta:
                logging.warning('WebSocket is ratelimited, waiting %.2f seconds', delta)
                await asyncio.sleep(delta)


class DiscordWebSocket:
    # web socket opt codes
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

    client: 'Client' = None
    socket: ClientWebSocketResponse = None
    token = None
    _zlib = zlib.decompressobj()
    _buffer = bytearray()
    sequence = None
    session_id = None
    _close_code = None

    def __init__(self, client):
        self.client = client
        self._rate_limiter = GatewayRateLimiter()
        self.heartbeat_manager: HeartbeatThread = None
        self.loop = client.loop
        pass

    async def send_as_json(self, payload: dict, ignore_rate_limit: bool = False):
        if not ignore_rate_limit:
            await self._rate_limiter.block()
        try:
            await self.socket.send_json(payload)
        except RuntimeError as e:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket) from e

    async def handle_message(self, data):
        if type(data) is bytes:
            self._buffer.extend(data)
            # zlib stream not finished
            if len(data) < 4 or data[-4:] != b'\x00\x00\xff\xff':
                return
            # data stream complete -> decompress
            data = self._zlib.decompress(self._buffer)
            data = data.decode('utf-8')
            # clear buffer
            self._buffer = bytearray()
        msg = utils.get_dict_from_json(data)

        op = msg.get('op')
        seq = msg.get('s')
        data = msg.get('d')
        event = msg.get('t')
        if seq is not None:
            if self.sequence is None or seq > self.sequence:
                self.sequence = seq

        if self.heartbeat_manager:
            self.heartbeat_manager.tick()

        if op == self.HELLO:
            self.heartbeat_manager = HeartbeatThread(self, data.get('heartbeat_interval') / 1000.0)
            logging.debug('received hello, send heartbeat')
            await self.send_as_json(self.heartbeat_manager.get_payload())
            self.heartbeat_manager.start()
            return
        if op == self.HEARTBEAT_ACK:
            if self.heartbeat_manager:
                self.heartbeat_manager.ack()
            # logging.debug('received heatbeat ack')
            return
        logging.debug(f'got Web Socket event: {str(msg)}')
        if op == self.RECONNECT:
            logging.debug(f'got a request to reconnect')
            await self.close()
            raise ReconnectWebSocket()
        if op == self.DISPATCH:
            if event == 'READY':
                self.sequence = msg.get('s')
                self.session_id = data.get('session_id')
                self.client._guilds = {}
                for guild in data['guilds']:
                    self.client._guilds[int(guild.get('id'))] = None
                logging.info(f'Connected to Gateway: {", ".join(data.get("_trace", []))} (Session ID: {self.session_id})')
            elif event == 'RESUMED':
                logging.info(f'fully resumed session {self.session_id}')
            else:
                logging.debug(f'got event: {event} (data: {str(data)})')
            self.loop.create_task(self.client.dispatch_gateway_event(event, data))
            return
        if op == self.INVALID_SESSION:
            if data is True:
                await self.close()
                raise ReconnectWebSocket()
            self.sequence = None
            self.session_id = None
            logging.info(f'session has been invalidated')
            await self.close(code=1000)
            raise ReconnectWebSocket(resume=False)
        logging.warning(f'unknown OP code {op}')

    async def close(self, code=4000):
        if self.heartbeat_manager:
            self.heartbeat_manager.stop()
            self.heartbeat_manager = None
        self._close_code = code
        await self.socket.close(code=code)

    async def send_heartbeat(self):
        await self.send_as_json(self.heartbeat_manager.get_payload())

    def _can_handle_close(self):
        return self.socket.close_code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014)

    async def poll_event(self):
        try:
            msg = await self.socket.receive()
            if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                await self.handle_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.ERROR:
                logging.error(f'received error {str(msg)}')
                raise msg.data
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                logging.debug(f'received message {str(msg.type)}')
                raise WebSocketClosure()
            else:
                logging.error(f'received unknown message: {str(msg)}')
        except (asyncio.TimeoutError, WebSocketClosure) as e:
            logging.error('poll timed out')
            if self.heartbeat_manager:
                self.heartbeat_manager.stop()
                self.heartbeat_manager = None
            if isinstance(e, asyncio.TimeoutError):
                logging.info('Timed out receiving packet. Attempting to reconnect.')
                raise ReconnectWebSocket() from None
            code = self._close_code or self.socket.close_code
            if self._can_handle_close():
                logging.info(f'Websocket closed with {self.socket.close_code}, attempting a reconnect.')
                raise ReconnectWebSocket() from None
            else:
                logging.info(f'Websocket closed with {self.socket.close_code}. can not reconnect')
                raise ConnectionClosed(self.socket, code=code) from None
            pass

        pass

    async def identify(self):
        d = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'compress': True,
                'large_threshold': 250,
                'shard': [self.client.shard_id, self.client.shard_count],
                'intents': self.client.intents.value,
                'properties': {
                    '$os': '',
                    '$browser': f'DisTee.py v{utils.VERSION}',
                    '$device': f'DisTee.py v{utils.VERSION}'
                },
                'presence': {
                    'status': self.client.presence_status.value
                }
            }
        }
        if self.client.activity is not None:
            d['d']['presence']['activities'] = [self.client.activity]
        await self.send_as_json(d)

    async def update_presence(self):
        d = {
            'op': self.PRESENCE_UPDATE,
            'd': {
                'status': self.client.presence_status.value
            }
        }
        if self.client.activity is not None:
            d['d']['activities'] = [self.client.activity]
        await self.send_as_json(d)

    async def request_guild_members(self, gid: int):
        d = {
            'op': self.REQUEST_GUILD_MEMBERS,
            'd': {
                'guild_id': gid,
                'limit': 0,
                'query': '',
                'presences': False
            }
        }
        await self.send_as_json(d)

    async def resume(self):
        d = {
            'op': self.RESUME,
            'd': {
                'token': self.token,
                'session_id': self.session_id,
                'seq': self.sequence
            }
        }
        await self.send_as_json(d)

    async def run(self, resume=False):
        self._close_code = None
        self._zlib = zlib.decompressobj()
        self._buffer = bytearray()
        gateway = await self.client.http.get_gateway()
        self.socket = await self.client.http.ws_connect(gateway)
        self.token = self.client.http.token

        # wait for HELLO
        await self.poll_event()

        if not resume:
            await self.identify()
        else:
            await self.resume()
        # actually run stuff 🎉
        while True:
            await self.poll_event()


