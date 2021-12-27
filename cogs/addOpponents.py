from brawlstats.errors import NotFoundError
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
      try: #sometimes it can't find club
        table = ClubTable(club_tag)
        messages = await table.create()
        club_name = client.get_club(club_tag).raw_data['name'] #ting
        channel = await guild.create_text_channel(club_name, category=category)
        for message in messages:
          await channel.send(f"```{message}```")
        self.client.guild_data[guild.id]['Opponents'].append({'tag': club_tag, 'name': club_name, 'channel': channel, 'table': table})
      except NotFoundError:
        await ctx.send(f'not found: {club_tag}')

def setup(client):
  client.add_cog(AddOpponents(client))