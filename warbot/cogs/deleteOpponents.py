from discord.ext import commands

class deleteOpponents(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases = ['d'])
  async def deleteOpponents(self, ctx):
    guild = ctx.guild
    channels = await guild.fetch_channels()

    for channel in channels:
      if not channel.category is None and channel.category.name == 'Opponents':
        await channel.delete()

    try:
      self.guild_data[guild.id]['Opponents'] = []
    except:
      pass

def setup(bot: commands.Bot):
  bot.add_cog(deleteOpponents(bot))