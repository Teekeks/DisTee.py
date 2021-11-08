
def flatten_error_dict(d, key=''):
    items = []
    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors = v['_errors']
            except KeyError:
                items.extend(flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(Exception):

    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        if isinstance(message, dict):
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = f'{base}\n{helpful}'
            else:
                self.text = base
        else:
            self.text = message
            self.code = 0

        super().__init__(f'{self.status} {self.response.reason} (error code: {self.code}) {self.text}')
    pass


class Forbidden(HTTPException):
    pass


class NotFound(HTTPException):
    pass


class DiscordServerError(HTTPException):
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


class InteractionException(Exception):
    pass


class WrongInteractionTypeException(InteractionException):
    pass
