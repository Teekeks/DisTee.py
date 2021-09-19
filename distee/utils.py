import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client

VERSION = 'indef'
GATEWAY_VERSION = 9
API_VERSION = 9


def get_dict_from_json(data) -> dict:
    return json.loads(data)


class Snowflake:

    def __init__(self, **args):
        self.id: int = int(args.get('id'))
        self._client: Client = args.get('_client')

    def __eq__(self, other):
        if isinstance(other, Snowflake):
            return self.id == other.id
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

