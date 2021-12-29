import brawlstats
from warbot.config import BS_TOKEN
from discord.ext import commands

class bsClient(brawlstats.Client, commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        brawlstats.Client.__init__(self, BS_TOKEN(), is_async=True, loop=bot.loop)
        
    def cog_unload(self):
        self.bot.loop.create_task(self.close())

def setup(bot: commands.Bot):
    bot.add_cog(bsClient(bot))