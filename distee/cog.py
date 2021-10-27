from .client import Client
from typing import Union, Optional
from .enums import Event


def event(name: Union[str, Event]):
    def decorator(self, func):
        n = name.value if isinstance(name, Event) else name
        if self.client._event_listener.get(n) is None:
            self.client._event_listener[n] = []
        self.client._event_listener[n].append(func)
        return func

    return decorator


def raw_event(self, name: str):
    def decorator(func):
        self.client.register_raw_gateway_event_listener(name, func)
        return func

    return decorator


def interaction_handler(self,
                        custom_id: Optional[str] = None):
    def decorator(func):
        self.client._interaction_handler[custom_id] = func
        return func

    return decorator


class Cog:

    def __init__(self, client: Client):
        self.client: Client = client


