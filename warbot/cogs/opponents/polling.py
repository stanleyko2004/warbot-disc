from typing import TYPE_CHECKING, Union
import asyncio

from discord.ext import commands

from .models import Player, Battle, Club, BattleType, Result

from datetime import datetime, timedelta

if TYPE_CHECKING:
    from warbot.cogs.bsClient import bsClient

class Poller:
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: bsClient = bot.get_cog('bsClient')
    
    async def initialize_club(self, tag: str):
        club_data = (await self.client.get_club(tag)).raw_data
        print(f"found {club_data['name']}({tag}), getting players")
        club_members = {}
        tasks = []
        for i, member_data in enumerate(club_data['members']):
            tasks.append(self.bot.loop.create_task(self.initialize_player(member_data, i+1)))
        club_members = {k:v for k,v in await asyncio.gather(*tasks)}
        print(f"{club_data['name']}({tag}) initialized")
        return Club(tag, club_data['name'], club_members)
        
    async def initialize_player(self, player_data: dict, rank: int):
        new_player = Player(tag = player_data['tag'], 
                            name = player_data['name'].encode("ascii", "ignore").decode(),
                            trophies = player_data['trophies'],
                            rank = rank
                            )
        battle_log_data = (await self.client.get_battle_logs(player_data['tag'])).raw_data
        if len(battle_log_data) > 0: #in case log wipes
            new_player.lastOnline = Poller.get_datetime(battle_log_data[0]['battleTime'])
            for battle_data in battle_log_data:
                if args := Poller.valid_battle(battle_data):
                    battle = Battle(*args)
                    for i in range(2):
                        for player_data in battle_data['battle']['teams'][i]:
                            battle.teams.append(player_data['tag'])
                    new_player.warBattles.append(battle)
        return player_data['tag'], new_player
    
    @staticmethod
    def valid_battle(battle: dict) -> Union[bool, tuple]:
        if not 'trophyChange' in battle['battle']: # gets rid of power league
            return None
        
        battle_time = Poller.get_datetime(battle['battleTime'])
        if (datetime.now() - battle_time).total_seconds() > 24 * 3600: #in time range
            return None
        
        if 'type' not in battle['battle']: # gets rid of boss fight
            return None
        
        if battle['battle']['type'] in {'teamRanked', 'soloRanked'}: # gets rid of ladder
            return (
                battle_time, 
                battle['battle']['trophyChange'], 
                BattleType(battle['battle']['type']), 
                Result(battle['battle']['result'])
            ) 
    
    @staticmethod
    def get_datetime(timestamp: str) -> datetime:
        return datetime.strptime(timestamp, '%Y%m%dT%H%M%S.%fZ') - timedelta(hours=8) #goddamn finland
    