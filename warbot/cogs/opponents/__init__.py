from typing import TYPE_CHECKING

import asyncio
import time
from datetime import datetime
import typing

import discord
from discord.channel import CategoryChannel, TextChannel
from discord.ext import commands, tasks
from discord.ext.commands import context

from brawlstats.errors import NotFoundError
from .polling import Poller
from .table import generate_message
from warbot.config import WAR_SCHEDULE

import warbot.cogs.database.models as mds
from warbot.cogs.bsClient.schema import *

if TYPE_CHECKING:
    from warbot.cogs.bsClient import BSClient
    from discord.guild import Guild

WAR_DISPLAY = 'test-Opponents'

class Opponents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: BSClient = self.bot.get_cog('BSClient')
        self.watcher.start()
        # self.watcher_task = self.client.loop.create_task(self.watcher())


    async def get_display(self, ctx: context.Context) -> CategoryChannel:
        guild: Guild = ctx.guild
        return discord.utils.get(guild.categories, name=WAR_DISPLAY) or await guild.create_category(WAR_DISPLAY)
    
    async def reset_display(self, ctx: context.Context) -> CategoryChannel:
        display = await self.get_display(ctx)
        text_channels: list[TextChannel] = display.channels
        await asyncio.gather(*[self.bot.loop.create_task(channel.delete())
                               for channel in text_channels])
        if not ctx.guild.id in self.bot.guild_data:
            self.bot.guild_data[ctx.guild.id] = {}
        self.bot.guild_data[ctx.guild.id]['display'] = None
        return display
    
    async def load_war(self, ctx: context.Context, war: mds.War):
        pass
    
    @commands.command(aliases = ['wload'])
    async def loadwar(self, ctx: context.Context, warId: int):
        guild: Guild = ctx.guild
        async with Poller(self.bot) as poller:
            war = poller.get_war(warId)
            if war is None:
                await ctx.send(f'war {warId} not found')
                return
            display = await self.reset_display(ctx)
                
            async def load_club(club_war: mds.Club_War):
                channel = await guild.create_text_channel(name=club_war.name, category=display)
                club_war_day = club_war.club_war_days.get(WAR_SCHEDULE.get_current_war_day(), list(club_war.club_war_days.values())[-1])
                await channel.send(generate_message(club_war_day))
                return club_war.club.tag, channel

            self.bot.guild_data[guild.id]['display'] = (warId, dict(await asyncio.gather(*[load_club(club_war) for club_war in war.club_wars])))
            
    class StartTime(commands.Converter):
        async def convert(self, ctx, arg: str):
            try:
                return datetime.fromisoformat(arg)
            except (TypeError, ValueError):
                raise commands.BadArgument(f'{arg} failed to parse (must be in iso format)')
    
    class ClubTag(commands.Converter):
        async def convert(self, ctx, tag: str) -> str:
            tag = tag.strip('#').upper()
            ALLOWED = '0289PYLQGRJCUV'
            
            invalid = [c for c in tag if c not in ALLOWED]
            if len(tag) < 3 or invalid:
                raise commands.BadArgument('Invalid tag')
            
            return '#' + tag
    
    @commands.command(aliases = ['aw'])
    async def addWar(self, ctx: context.Context, tags: commands.Greedy[ClubTag], *, start_time: StartTime = None):
        start = time.time()
        async with Poller(self.bot) as poller:
            war = poller.init_war(start_time)
            poller.add_clubs(war, tags)
            await poller.update_war(war)
        
        assert war
        
        await ctx.send(f'done in {time.time() - start} secs')
    
    @commands.command(aliases = ['p'])
    async def getPlayer(self, ctx: context.Context, id):
        try:
            id = await self.client.get_player(id)
        except NotFoundError as e:
            id = str(e)
        print(id)
        await ctx.send(id)
    
    @tasks.loop(minutes=5.0)
    async def watcher(self):
        print('polling', datetime.now().strftime("%H:%M:%S"))
        start = time.time()
        poller = Poller(self.bot)
        guilds = self.bot.guild_data
        
        for guild in guilds.values():
            if guild.get('display') is None:
                continue
            warId = guild['display'][0]
            async with Poller(self.bot) as poller:
                war = poller.get_war(warId)
                await poller.update_war(war)
                
                async def update_club_war_channel(club_war_day: mds.Club_War_Day, channel: TextChannel):
                    current_message = (await channel.history(limit=1, oldest_first=True).flatten())[0]
                    if (new_message := generate_message(club_war_day)) != current_message.content:
                        await current_message.edit(content=new_message)
                        print(f"updating {club_war_day.club_war.name}")
                    else:
                        print(f'nothing new for {club_war_day.club_war.name} :(')
                
                update_tasks = []
                for club_war in war.club_wars:
                    club_war_day = club_war.club_war_days.get(WAR_SCHEDULE.get_current_war_day(), list(club_war.club_war_days.values())[-1])
                    update_tasks.append(self.bot.loop.create_task(
                        update_club_war_channel(club_war_day, guild['display'][1][club_war_day.club_war.club.tag])
                    ))
                await asyncio.gather(*update_tasks)
        print(f'polling complete in {time.time() - start} secs')

    @watcher.before_loop
    async def before_watcher(self):
        print('loop boi not ready')
        await self.bot.wait_until_ready()
        print('loop boi ready')
    
    # async def watcher(self):
    #     print('loop boi not ready')
    #     await self.bot.wait_until_ready()
    #     print('loop boi ready')
    #     while True:
    #         print('polling', datetime.now().strftime("%H:%M:%S"))
    #         start = time.time()
    #         poller = Poller(self.bot)
    #         guilds = self.bot.guild_data

    #         async def update_opponent(opponent: tuple[TextChannel, oldmodels.Club]):
    #             channel: TextChannel = opponent[0]
    #             club = await poller.update_club(opponent[1], update_players=True, update_logs=True)
    #             # current_messages = await channel.history(limit=50, oldest_first=True).flatten()
    #             # flag = True
    #             # for index, message in enumerate(generate_message(club)):
    #             #     if current_messages[index].content != f'```{message}```':
    #             #         flag = False
    #             #         print(f"updating {club.name} {index}")
    #             #         await current_messages[index].edit(content=f'```{message}```')
    #             # if flag:
    #             #     print(f'nothing new for {club.name} :(')
    #             current_message = (await channel.history(limit=1, oldest_first=True).flatten())[0]
    #             if (new_message := generate_message(club)) != current_message.content:
    #                 await current_message.edit(content=new_message)
    #                 print(f"updating {club.name}")
    #             else:
    #                 print(f'nothing new for {club.name} :(')

    #         for guild in guilds.values():
    #             tasks = []
    #             for opponent in guild['Opponents']:
    #                 tasks.append(update_opponent(opponent))
    #                 # channel: TextChannel = opponent[0]
    #                 # club = await poller.update_club(opponent[1], update_players=True, update_logs=True)
    #                 # current_messages = await channel.history(limit=50, oldest_first=True).flatten()
    #                 # flag = True
    #                 # for index, message in enumerate(generate_message(club)):
    #                 #     if current_messages[index].content != f'```{message}```':
    #                 #         flag = False
    #                 #         print(f"updating {club.name} {index}")
    #                 #         await current_messages[index].edit(content=f'```{message}```')
    #                 # if flag:
    #                 #     print(f'nothing new for {club.name} :(')
    #             await asyncio.gather(*tasks)
    #             print(f'polling complete in {time.time() - start} secs')
    #         await asyncio.sleep(5*60)

def setup(bot: commands.Bot):
    bot.add_cog(Opponents(bot))