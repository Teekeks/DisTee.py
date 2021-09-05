from distee.client import Client
from distee.user import User
from pprint import pprint
from distee.flags import Intents
import logging
from distee.message import Message
from distee.flags import UserFlags
from distee.utils import Snowflake
import json
from distee.channel import GuildChannel

logging.basicConfig(level=logging.DEBUG)

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)

intents = Intents.all()
client = Client()


@client.event('message')
async def message_was_send(msg: Message):
    if msg.author != client.user:
        embed = {
            'description': 'lorem ipsum',
            'title': 'Data',
            'color': 0x00cc00,
            'fields': [
                {
                    'name': 'Cached Users',
                    'value': str(len(client._users))
                }, {
                    'name': 'Guild Members',
                    'value': str(len(msg.guild._members))
                }, {
                    'name': 'User Flags',
                    'value': ', '.join([flag.name for flag in UserFlags if flag in msg.author.public_flags])
                }
            ]
        }
        await msg.channel.send(content=f'Hello {msg.author.username} from {msg.guild.name}!',
                               reply_to=msg,
                               embeds=[embed])


@client.raw_event('MESSAGE_CREATE')
async def cool_raw_event(data: dict):
    usr = await client.fetch_user(Snowflake(id=data['author']['id']))
    pprint(usr.public_flags)
    # pprint(usr.public_flags.flag_list)

client.run(cfg['token'], intents=intents)
