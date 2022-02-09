from .utils import Snowflake
from typing import Optional


class Attachment(Snowflake):

    __slots__ = [
        'filename',
        'description',
        'content_type',
        'size',
        'url',
        'proxy_url',
        'height',
        'width',
        'ephemeral'
    ]

    def __init__(self, **data):
        super(Attachment, self).__init__(**data)
        self.filename: str = data.get('filename')
        self.description: Optional[str] = data.get('description')
        self.content_type: Optional[str] = data.get('content_type')
        self.size: int = data.get('size')
        self.url: str = data.get('url')
        self.proxy_url: str = data.get('proxy_url')
        self.height: Optional[int] = data.get('height')
        self.width: Optional[int] = data.get('width')
        self.ephemeral: Optional[bool] = data.get('ephemeral')

