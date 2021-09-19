from .utils import Snowflake


class Application(Snowflake):

    def __init__(self, **data):
        super(Application, self).__init__(**data)
        self.name: str = data.get('name')
        self.description: str = data.get('description')
        # TODO: add all from this: https://discord.com/developers/docs/resources/application#application-object
