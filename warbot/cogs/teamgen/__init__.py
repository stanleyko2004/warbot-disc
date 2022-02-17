from typing import TYPE_CHECKING, Union

from warbot.config import DEFAULT_CLUB_TAG

import asyncio
import brawlstats

import discord
from discord.ext import commands
from discord.ext.commands import context
from warbot.cogs.opponents import Opponents
from warbot.cogs.teamgen.stackedness import check_player
from warbot.cogs.teamgen.team_gen import gen_configuration
from warbot.cogs.teamgen.kernel import find_best_teams_index
from warbot.cogs.teamgen.combos import nth_team_list, num_team_lists
from warbot.cogs.teamgen.owners import OWNERS, OWNER_MAP, ALL_OWNERS

if TYPE_CHECKING:
    from warbot.cogs.bsClient import BSClient

class Teamgen(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: BSClient = self.bot.get_cog('BSClient')
    
    async def get_scores(self):
        players: brawlstats.Members= await self.client.get_club_members('2PLUPQPV')
        # for p in players.raw_data:
        #     print(p['tag'], p['name'])
        result = await asyncio.gather(*[check_player(self.client, p['tag']) for p in players])
        result = sorted(result, key=lambda p: p[1], reverse=True)
        return result
    
    @commands.command(aliases = ['stack'])
    async def stackedness(self, ctx: context.Context, clubTag: Opponents.Tag = DEFAULT_CLUB_TAG):
        result = await self.get_scores()
        message = (','.join([str(p.score) + ' ' + p.name] + 
                            [str(b.score) + b.name + str(b.power) 
                             for b in p.brawlers])
                   for p in result)
        chunk = '```\n'
        chunk_len = 4
        for line in message:
            if chunk_len + len(line) > 2000 - 3:
                chunk += '```'
                await ctx.send(chunk)
                chunk = '```\n'
                chunk_len = 4
            else:
                chunk += '\n' + line
                chunk_len += len(line)
        if chunk_len > 4:
            chunk += '```'
            await ctx.send(chunk)
    
    @commands.command(aliases = ['vo'])
    async def viewowners(self, ctx: context.Context, clubTag: Opponents.Tag = DEFAULT_CLUB_TAG):
        members: brawlstats.Members= await self.client.get_club_members(clubTag)
        
        inferiors = []
        message = ''
        for member in members:
            if member['tag'] in ALL_OWNERS:
                message += f"{member['name']:<20} {member['tag']:<15} {member['tag'] in OWNER_MAP}\n"
            else:
                inferiors.append(f"{member['name']} ({member['tag']})")
        
        await ctx.send('```' + message + '\n' +
                       'Inferiors: ' + ', '.join(inferiors) + '```')
        
    
    @commands.command(aliases = ['eo'])
    async def editowners(self, ctx: context.Context, action: str, playerTags: commands.Greedy[Opponents.Tag], *args):
        if action not in ('-d', '-e'):
            await ctx.send(f'invalid action: {action}')
            return
        
        if not playerTags and '-a' in args:
            playerTags = (t for t in ALL_OWNERS)
        
        unfound = []
        modified = []
        for playerTag in playerTags:
            if action == '-d':
                if playerTag in OWNER_MAP:
                    del OWNER_MAP[playerTag]
                    modified.append(playerTag)
            else:
                if (owners := ALL_OWNERS.get(playerTag)):
                    OWNER_MAP[playerTag] = owners
                    modified.append(playerTag)
                else:
                    unfound.append(playerTag)
        
        await ctx.send('```' + 'modified ' + ', '.join(modified) + '\n' + 
                       'unfound: ' ', '.join(unfound) + '```')
        
                
    @commands.command(aliases = ['ti'])
    async def teamsinfo(self, ctx: context.Context):
        players = await self.get_scores()
        config = gen_configuration(players)
        n = num_team_lists(*config)
        num_teams = min(map(len, config))
        await ctx.send(
            f'```Available players: {len(OWNER_MAP)}\n'
            f'Number of teams: {num_teams}\n'
            f'Permutations per cycle: {n:,}```'
            )
    
    @commands.command(aliases = ['teams'])
    async def teamgen(self, ctx: context.Context, cycles: int = 1, clubTag: Opponents.Tag = DEFAULT_CLUB_TAG):
        async with ctx.typing():
            players = await self.get_scores()
            
            best_score = 0
            best_teams = []
            for _ in range(cycles):
                c = gen_configuration(players, True)
                i, score = find_best_teams_index(c, 256, 256)
                if score > best_score:
                    best_score = score
                    best_teams = list(nth_team_list(i, *c))
            
            await ctx.send('\n'.join(['```'] + 
                                    [','.join([p.name for p in t]) for t in best_teams] + 
                                    [str(best_score)] + 
                                    ['```']))
                

# class PlayerToggleButton(discord.ui.Button['EditOwners']):
#     def __init__(self, playerTag: str, state: bool):
#         super().__init__()
#     async def callback(self, interaction: discord.Interaction):
#         pass
    
# class EditOwners(discord.ui.View):
#     def __init__(self):
#         super().__init__()
        

def setup(bot: commands.Bot):
    bot.add_cog(Teamgen(bot))