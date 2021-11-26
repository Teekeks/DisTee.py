from .utils import *


class Route:
    BASE_URL = f'https://discord.com/api/v{API_VERSION}'

    def __init__(self, method: str, path: str, **parameters):
        self.path = path
        self.method = method
        self.url = self.BASE_URL + self.path

        if parameters:
            for k, v in parameters.items():
                self.url = self.url.replace('{'+k+'}', str(v.id) if isinstance(v, Snowflake) else str(v))

        self.channel_id = parameters.get('channel_id')
        if isinstance(self.channel_id, Snowflake):
            self.channel_id = self.channel_id.id
        self.guild_id = parameters.get('guild_id')
        if isinstance(self.guild_id, Snowflake):
            self.guild_id = self.guild_id.id

    @property
    def bucket(self):
        return f'{self.channel_id}:{self.guild_id}:{self.path}'
