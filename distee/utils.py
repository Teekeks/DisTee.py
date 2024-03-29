import datetime
import json
from typing import TYPE_CHECKING, Union


if TYPE_CHECKING:
    from .base_client import BaseClient

VERSION = 'indef'
GATEWAY_VERSION = 10
API_VERSION = 10


def get_dict_from_json(data) -> dict:
    return json.loads(data)


def get_json_from_dict(data) -> str:
    return json.dumps(data)


def command_lists_equal(local, remote) -> bool:
    if len(local) != len(remote):
        return False
    for l in local:
        found = False
        for r in remote:
            if l == r:
                found = True
                break
        if not found:
            return False
    return True


def get_components(comps):
    return [x if isinstance(x, dict) else x.to_json() for x in comps] if comps is not None else None


class Snowflake:

    __slots__ = [
        'id',
        '_client'
    ]

    def __init__(self, **args):
        self.id: int = int(args.get('id')) if args.get('id') is not None else None
        self._client: BaseClient = args.get('_client')

    def __eq__(self, other):
        if isinstance(other, Snowflake):
            return self.id == other.id
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_creation_datetime(self) -> datetime.datetime:
        timestamp = ((self.id >> 22) + 1420070400000) / 1000
        return datetime.datetime.fromtimestamp(timestamp)


def snowflake_id(s: Union[int, Snowflake]) -> int:
    return s if isinstance(s, int) else s.id


def snowflake_or_none(id):
    return Snowflake(id=id) if id is not None else None
