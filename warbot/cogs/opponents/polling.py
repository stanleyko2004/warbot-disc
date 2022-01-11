from typing import TYPE_CHECKING, Union, TypedDict
import asyncio
from dataclasses import dataclass, field

import discord
from discord.ext import commands

from warbot.cogs.database.models import BattleType, Result, War, Day, Player, Battle, Club, Club_War, Club_War_Player, Club_War_Day_Player
from warbot.config import WAR_SCHEDULE

from datetime import datetime, timedelta

if TYPE_CHECKING:
    from warbot.cogs.bsClient import BSClient
    
from warbot.cogs.bsClient.schema import *
from brawlstats.errors import NotFoundError

from sqlalchemy.orm.session import Session, sessionmaker

class Poller:
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: BSClient = bot.get_cog('BSClient')
        self.db: sessionmaker = bot.get_cog('DBSession')
    
    async def __aenter__(self):
        self.dbcontext = self.db.begin()
        self.dbsession: Session = self.dbcontext.__enter__()
        return self
    
    async def __aexit__(self, *args):
        self.dbcontext.__exit__(*args)
        self.dbsession = None
    
    def init_war(self, start_time: datetime = None) -> War:
        if start_time is None:
            start_time = WAR_SCHEDULE.get_current_start()
        
        war = War(start_time)
        for day_start in WAR_SCHEDULE.get_war_days(start_time):
            war.add_day(Day(day_start))
        
        self.dbsession.add(war)
        # self.dbsession.flush()
        return war
    
    def add_clubs(self, war: War, club_tags: list[str]):
       for club_tag in club_tags:
           war.add_club(self.get_club(club_tag))
       
    def get_war(self, warId: int) -> Union[War, None]:
        return self.dbsession.get(War, warId)
    
    def get_club(self, club_tag: str) -> Club:
        club = self.dbsession.get(Club, club_tag)
        if club is None:
            club = Club(club_tag)
            self.dbsession.add(club)
            return club
        else:
            return club
    
    def get_player(self, player_tag: str) -> Player:
        player = self.dbsession.get(Player, player_tag)
        if player is None:
            player = Player(player_tag)
            self.dbsession.add(player)
            if player is None:
                assert True
            return player
        else:
            if player is None:
                assert True
            return player
    
    def get_battle(self, battle_data: BattleData, club_tag: str) -> Battle:
        args = {
            'battleTime': Poller.get_datetime(battle_data['battleTime']),
            'type': BattleType(battle_data['battle']['type']),
            'result': Result(battle_data['battle']['result']),
            'trophyChange': battle_data['battle']['trophyChange'],
            'starPlayerTag': battle_data['battle']['starPlayer']['tag']
        }
        try:
            battles = self.dbsession.query(Battle).filter_by(**args).all()
        except AssertionError:
            pass
        if len(battles) > 1: # if 2 clubs faced each other
            battles = [b for b in battles if b.club_war.club.tag == club_tag]

        elif len(battles) == 0: # didn't find any
            battle = Battle(**args)
            self.dbsession.add(battle)
            # self.dbsession.flush()
        elif len(battles) == 1: # found one
            battle = battles[0]
            # battle, = battles
        elif len(battles) > 1: # afaik ths can only happen if 2 teams from the same club face each other
            raise ValueError('hopefully this never happens')
        
        return battle
    
    async def update_war(self, war: War):
        await asyncio.gather(*[self.update_club_war(club_war) for club_war in war.club_wars])
        return war
    
    async def update_club_war(self, club_war: Club_War, club_data: ClubData = None):
        if club_data is None:
            club_data = (await self.client.get_club(club_war.club.tag)).raw_data
        print(f"found {club_data['name']}({club_war.club.tag}), fetching logs")
        
        club_war.name = club_data['name']
        club_war.trophies = club_data['trophies']
        
        player_updates = []
        for i, member_data in enumerate(club_data['members']):
            club_war_player = club_war.club_war_players.get(member_data['tag'])
            if club_war_player is None:
                club_war_player = club_war.add_player(self.get_player(member_data['tag']))
                if club_war_player is None:
                    assert True
            if club_war_player is None:
                assert True
            player_updates.append(self.bot.loop.create_task(self.update_club_war_player(club_war_player, member_data, i+1)))
        await asyncio.gather(*player_updates) # ^ all that can be one lined but im restricting myself
        
        battle_logs_data: list[list[BattleData]] = list(map(lambda b: b.raw_data, 
                                                     await asyncio.gather(*[self.client.get_battle_logs(tag) 
                                                                            for tag in club_war.club_war_players])))
        for (player_tag, club_war_player), battle_log_data in zip(club_war.club_war_players.items(), battle_logs_data):
            club_war_player.lastOnline = Poller.get_datetime(battle_log_data[0]['battleTime'])
            for battle_data in battle_log_data:
                if Poller.is_valid_battle(battle_data):
                    battle = self.get_battle(battle_data, club_war.club.tag)
                    club_war_day = club_war.club_war_days.get(WAR_SCHEDULE.get_current_war_day(battle.battleTime))
                    if club_war_day is None:
                        self.dbsession.expunge(battle)
                        continue
                    club_war_day_player = club_war_day.club_war_day_players[player_tag]
                    if player_tag not in battle.club_war_day_player_battles:
                        b = battle.add_player(club_war_day_player)
                        assert b
            for club_war_day in club_war.club_war_days.values():
                club_war_day.redTicketsUsed = club_war_day.goldenTicketsUsed = 0
                club_war_day_player = club_war_day.club_war_day_players[player_tag]
                club_war_day_player_battles = sorted(club_war_day_player.club_war_day_player_battles, 
                                                        key=lambda b: b.battle.battleTime)
                for cwdpb, v in zip(club_war_day_player_battles, (False, False, True, True)):
                    cwdpb.isGolden = v
                    if v:
                        club_war_day.goldenTicketsUsed += 1
                    else:
                        club_war_day.redTicketsUsed += 1
        print(f"{club_data['name']} updated")
        return club_war
        
    
    async def update_club_war_player(self, 
                                     club_war_player: Club_War_Player, 
                                     member_data: Union[MemberData, PlayerData] = None, 
                                     rank: int = None) -> Club_War_Player:
        if member_data is None:
            member_data: PlayerData = (await self.client.get_player(club_war_player.playerTag)).raw_data
        
        if club_war_player is None:
            assert True
        
        club_war_player.name = member_data['name']
        club_war_player.trophies = member_data['trophies']
        club_war_player.rank = rank
        
        return club_war_player
    
    @staticmethod
    def is_valid_battle(battle: BattleData) -> bool:
        if not 'trophyChange' in battle['battle']: # gets rid of power league
            return False
        
        if 'type' not in battle['battle']: # gets rid of boss fight
            return False
        
        if battle['battle']['type'] in {'teamRanked', 'soloRanked'}: # gets rid of ladder
            return True
    
    @staticmethod
    def get_datetime(timestamp: str) -> datetime:
        return datetime.strptime(timestamp, '%Y%m%dT%H%M%S.%fZ')
    