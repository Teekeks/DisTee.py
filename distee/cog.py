from .client import Client
from typing import Union, Optional
from .enums import Event


class Cog:

    def __init__(self, client: Client):
        self.client: Client = client
        # lets register listener
        events = self.__get_events()
        for event in events['full']:
            name = getattr(event, '__event_name__')
            n = name.value if isinstance(name, Event) else name
            if self.client._event_listener.get(n) is None:
                self.client._event_listener[n] = []
            self.client._event_listener[n].append(event)
        for event in events['raw']:
            name = getattr(event, '__event_name__')
            self.client.register_raw_gateway_event_listener(name, event)
        for event in events['interaction']:
            custom_id = getattr(event, '__event_name__')
            self.client._interaction_handler[custom_id] = event

    def __get_events(self):
        vals = {
            'full': [],
            'raw': [],
            'interaction': []
        }
        for v in dir(self):
            value = getattr(self, v)
            try:
                getattr(value, '__event_name__')
                t = getattr(value, '__event_type__')
            except AttributeError:
                continue
            else:
                vals[t].append(value)
        return vals

    @classmethod
    def event(cls, name: Union[str, Event]):
        def decorator(func):
            func.__event_name__ = name
            func.__event_type__ = 'full'
            return func
        return decorator

    @classmethod
    def raw_event(cls, name: str):
        def decorator(func):
            func.__event_name__ = name
            func.__event_type__ = 'raw'
            return func

        return decorator

    @classmethod
    def interaction_handler(cls,
                            custom_id: Optional[str] = None):
        def decorator(func):
            func.__event_name__ = custom_id
            func.__event_type__ = 'interaction'
            return func

        return decorator


