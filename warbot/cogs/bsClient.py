import brawlstats
from warbot.config import BS_TOKEN
from discord.ext import commands
import backoff

class BSClient(brawlstats.Client, commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        brawlstats.Client.__init__(self, BS_TOKEN(), is_async=True, loop=bot.loop)
    def cog_unload(self):
        self.bot.loop.create_task(self.close())

    def serv_backoff_hdlr(details):
        print(f"ServerError backoff: {details['wait']:0.1f} secs after {details['tries']} tries")

    def limit_backoff_hdlr(details):
        print(f"RateLimit backoff: {details['wait']:0.1f} secs after {details['tries']} tries")

    def success_hdlr(details):
        if details['tries'] > 1:
            print(f"success: {details['elapsed']=}, {details['tries']=}")

    # deal with rate limits
    @backoff.on_exception(backoff.expo,
                          brawlstats.ServerError,
                          max_tries=5,
                          on_backoff=serv_backoff_hdlr,
                          # on_success=success_hdlr
                          )
    @backoff.on_exception(backoff.expo,
                          brawlstats.RateLimitError,
                          max_tries=10,
                          on_backoff=limit_backoff_hdlr,
                        #   on_success=success_hdlr
                          )
    async def _arequest(self, url, use_cache=False):
        """Async method to request a url."""
        return await brawlstats.Client._arequest(self, url, use_cache)

def setup(bot: commands.Bot):
    bot.add_cog(BSClient(bot))