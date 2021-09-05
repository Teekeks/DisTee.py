
class HTTPException(Exception):
    pass


class ClientException(Exception):
    pass


class GatewayNotFound(Exception):
    pass


class WebSocketClosure(Exception):
    pass


class ReconnectWebSocket(Exception):
    pass


class ConnectionClosed(Exception):
    pass
