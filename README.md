# DisTee.py
Python wrapper for the Discord API

## Please note that this library is not intended for public usage!
**This library only contains the parts of the Discord API that I need for my personal projects and breaking changes can and will occur without any notice.**
if you still insist on using it despite these warnings, you can do so using this:

```py

from distee.client import Client
from distee.cog import Cog
from distee.guild import Guild
from distee.enums import Event

client = Client()


class MyCog(Cog):
    def register():
      ap = ApplicationCommand(
            name='ping',
            description='A ping command')
      self.client.register_command(ap, self.handle_ping, True, None)  # register as global slash command
   
   
   async def handle_ping(inter: Interaction):
       await inter.send('Pong')
   
   # Example Event handler
   @Cog.event(Event.GUILD_JOINED)
   async def on_server_join(guild: Guild):
       print(f'Joined guild {guild.name}!')
       
   
   # example raw gateway event
   @Cog.raw_event('READY'):
   async def on_ready_event(data: dict):
       print('Got the raw ready event!')


cog = MyCog(client)
cog.register()
client.run('my_cool_discord_token')
```
