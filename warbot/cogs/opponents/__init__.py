from typing import TYPE_CHECKING

import asyncio
import time
from datetime import datetime

import discord
from discord.channel import CategoryChannel, TextChannel
from discord.ext import commands
from discord.ext.commands import context

from brawlstats.errors import NotFoundError
from .models import Club
from .polling import Poller
from .table import generate_message

if TYPE_CHECKING:
    from warbot.cogs.bsClient import BSClient
    from discord.guild import Guild

OPPONENTS_CATEGORY = 'Opponents'

class Opponents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: BSClient = self.bot.get_cog('BSClient')
        self.watcher_task = self.client.loop.create_task(self.watcher())

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
        if (category := discord.utils.get(guild.categories, name=OPPONENTS_CATEGORY)) is None:
            category = await guild.create_category(OPPONENTS_CATEGORY)

        assert category

        #TODO add guild.id to database
        if not guild.id in self.bot.guild_data:
            self.bot.guild_data[guild.id] = {}
        self.bot.guild_data[guild.id]['Opponents'] = []

        #TODO initialize table for each added opponent club
        poller = Poller(self.bot)
        start = time.time()

        async def init_channel(club_tag):
            club = await poller.initialize_club(club_tag)
            channel = await guild.create_text_channel(name=club.name, category=category)
            # for message in generate_message(club):
            #     await channel.send(f'```{message}```')
            await channel.send(generate_message(club))
            return channel, club

        tasks = []
        for club_tag in tags.split(' '):
            tasks.append(self.bot.loop.create_task(init_channel(club_tag)))
        self.bot.guild_data[guild.id]['Opponents'] += await asyncio.gather(*tasks)

        await ctx.send(f'done in {time.time() - start} secs')

    @commands.command(aliases = ['d'])
    async def deleteOpponents(self, ctx: context.Context):
        guild: Guild = ctx.guild

        opponents_category: CategoryChannel = discord.utils.get(guild.categories, name=OPPONENTS_CATEGORY)
        if opponents_category is None:
            await ctx.send('opponents channel does not exist')
            return

        channels: list[TextChannel] = opponents_category.channels
        # opponents: list[tuple[TextChannel, Club]] = self.bot.guild_data[guild.id]['Opponents']
        deletion_tasks = [self.bot.loop.create_task(channel.delete()) for channel in channels]
        # deletion_tasks = [delete_opponent(opponent) for opponent in opponents]
        await asyncio.gather(*deletion_tasks)
        await ctx.send('opponents reset')

    async def watcher(self):
        print('loop boi not ready')
        await self.bot.wait_until_ready()
        print('loop boi ready')
        while True:
            print('polling', datetime.now().strftime("%H:%M:%S"))
            start = time.time()
            poller = Poller(self.bot)
            guilds = self.bot.guild_data

            async def update_opponent(opponent: tuple[TextChannel, Club]):
                channel: TextChannel = opponent[0]
                club = await poller.update_club(opponent[1], update_players=True, update_logs=True)
                # current_messages = await channel.history(limit=50, oldest_first=True).flatten()
                # flag = True
                # for index, message in enumerate(generate_message(club)):
                #     if current_messages[index].content != f'```{message}```':
                #         flag = False
                #         print(f"updating {club.name} {index}")
                #         await current_messages[index].edit(content=f'```{message}```')
                # if flag:
                #     print(f'nothing new for {club.name} :(')
                current_message = await channel.history(limit=1, oldest_first=True).flatten()[0]
                if new_message := generate_message(club) != current_message.content:
                    await current_message.edit(content=new_message)
                    print(f"updating {club.name}")
                else:
                    print(f'nothing new for {club.name} :(')

            for guild in guilds.values():
                tasks = []
                for opponent in guild['Opponents']:
                    tasks.append(update_opponent(opponent))
                    # channel: TextChannel = opponent[0]
                    # club = await poller.update_club(opponent[1], update_players=True, update_logs=True)
                    # current_messages = await channel.history(limit=50, oldest_first=True).flatten()
                    # flag = True
                    # for index, message in enumerate(generate_message(club)):
                    #     if current_messages[index].content != f'```{message}```':
                    #         flag = False
                    #         print(f"updating {club.name} {index}")
                    #         await current_messages[index].edit(content=f'```{message}```')
                    # if flag:
                    #     print(f'nothing new for {club.name} :(')
                await asyncio.gather(*tasks)
                print(f'polling complete in {time.time() - start} secs')
            await asyncio.sleep(5*60)

def setup(bot: commands.Bot):
    bot.add_cog(Opponents(bot))