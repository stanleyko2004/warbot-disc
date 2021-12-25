import discord
from discord.ext import commands
from client import client #ting

class AddOpponents(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command(aliases = ['o'])
  async def addOpponents(self, ctx, *, name):
    guild = ctx.guild

    #creating category if not there
    category = discord.utils.get(guild.categories, name='Opponents')
    if category is None:
        category = await guild.create_category('Opponents')

    #creating channel
    channel = await guild.create_text_channel(name, category=category)

    #send the initial state
    channel.

def setup(client):
  client.add_cog(AddOpponents(client))