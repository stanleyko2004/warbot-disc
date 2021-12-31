from typing import TYPE_CHECKING

import asyncio
import time

import discord
from discord.channel import CategoryChannel, TextChannel
from discord.ext import commands
from discord.ext.commands import context

from brawlstats.errors import NotFoundError
from .polling import Poller

if TYPE_CHECKING:
    from warbot.cogs.bsClient import BSClient
    from discord.guild import Guild

OPPONENTS_CATEGORY = 'Opponents'

class Opponents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: BSClient = self.bot.get_cog('BSClient')
        
    @commands.command(aliases = ['p'])
    async def getPlayer(self, ctx: context.Context, id):
        try:
            id = await self.client.get_player(id)
        except NotFoundError as e:
            id = str(e)
        print(id)
        await ctx.send(id)

            
    @commands.command(aliases = ['o'])
    async def addOpponents(self, ctx: context.Context, *, tags: str):
        guild: Guild = ctx.guild
        
        #ensure opponents category exists
        if discord.utils.get(guild.categories, name=OPPONENTS_CATEGORY) is None:
            await guild.create_category(OPPONENTS_CATEGORY)
        
        #TODO add guild.id to database
        if not guild.id in self.bot.guild_data:
            self.bot.guild_data[guild.id] = {}
        self.bot.guild_data[guild.id]['Opponents'] = []
        
        #TODO initialize table for each added opponent club
        poller = Poller(self.bot)
        start = time.time()
        tasks = []
        for club_tag in tags.split(' '):
            tasks.append(self.bot.loop.create_task(poller.initialize_club(club_tag)))

        clubs = await asyncio.gather(*tasks)
        assert clubs
        await ctx.send(f'done in {time.time() - start} secs')

    @commands.command(aliases = ['d'])
    async def deleteOpponents(self, ctx: context.Context):
        guild: Guild = ctx.guild
        
        opponents_category: CategoryChannel = discord.utils.get(guild.categories, name=OPPONENTS_CATEGORY)
        if opponents_category is None:
            await ctx.send('opponents channel does not exist')
            return
        
        channels: list[TextChannel] = opponents_category.channels
        deletion_tasks = [self.bot.loop.create_task(channel.delete()) for channel in channels]
        await asyncio.gather(*deletion_tasks)
        await ctx.send('opponents reset')
        

def setup(bot: commands.Bot):
    bot.add_cog(Opponents(bot))