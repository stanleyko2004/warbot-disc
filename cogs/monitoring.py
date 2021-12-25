import discord
from discord.ext import tasks, commands
from client import client #ting

class Monitoring(commands.Cog):
  def __init__(self, client):
    self.index = 0
    self.client = client
    self.watcher.start()

  @tasks.loop(seconds=5.0)
  async def watcher(self):
    guilds = self.client.guilds
    for guild in guilds:
      for category, channels in guild.by_category():
        if category.name == 'Opponents':
          for channel in channels:
            print(channel)
          break
    self.index += 1

  @watcher.before_loop
  async def before_watcher(self):
    print('waiting...')
    await self.client.wait_until_ready()

def setup(client):
  client.add_cog(Monitoring(client))