from datetime import datetime
from brawlstats.errors import NotFoundError
from util import ClubTable
from discord.ext import tasks, commands

class Monitoring(commands.Cog):
  def __init__(self, client):
    self.index = 0
    self.client = client
    self.watcher.start()

  @tasks.loop(minutes=5.0)
  async def watcher(self):
    print('polling', datetime.now().strftime("%H:%M:%S"))
    guilds = self.client.guild_data
    for guild in guilds.values():
      for opponent in guild['Opponents']:
        table = opponent['table']
        new_messages = await table.create()
        channel = opponent['channel']
        current_messages = await channel.history(limit=50, oldest_first=True).flatten()
        flag = True
        for index, message in enumerate(new_messages):
          if current_messages[index].content != f'```{message}```':
            flag = False
            print('something new!')
            await current_messages[index].edit(content=f'```{message}```')
        if flag:
          name = opponent['name']
          print(f'nothing new for {name} :(')

  @watcher.before_loop
  async def before_watcher(self):
    print('loop boi not ready')
    await self.client.wait_until_ready()
    print('loop boi ready')

def setup(client):
  client.add_cog(Monitoring(client))