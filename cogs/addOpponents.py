import discord
from discord.ext import commands

######ting
from client import client
from util import ClubTable
######

class AddOpponents(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command(aliases = ['o'])
  async def addOpponents(self, ctx, *, tags):
    guild = ctx.guild

    #creating category if not there
    category = discord.utils.get(guild.categories, name='Opponents')
    if category is None:
      category = await guild.create_category('Opponents')

    #initialize guild opponents
    if not guild.id in self.client.guild_data:
      self.client.guild_data[guild.id] = {}
    self.client.guild_data[guild.id]['Opponents'] = []

    #creating channels
    tags = tags.split(' ')
    for club_tag in tags:
      club_name = client.get_club(club_tag).raw_data['name'] #ting
      channel = await guild.create_text_channel(club_name, category=category)
      self.client.guild_data[guild.id]['Opponents'].append({'tag': club_tag, 'name': club_name, 'channel': channel})

    #sending initial tables
    for opponent in self.client.guild_data[guild.id]['Opponents']:
      table = ClubTable(opponent['tag'])
      messages = await table.create()
      for message in messages[:10]:
        await opponent['channel'].send(f"```{message}```")

def setup(client):
  client.add_cog(AddOpponents(client))