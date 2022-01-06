from typing import TYPE_CHECKING, Union, TypedDict
import asyncio
from dataclasses import dataclass, field

from discord.ext import commands

from .models import Player, Battle, Club, BattleType, Result

from datetime import datetime, timedelta

if TYPE_CHECKING:
    from warbot.cogs.bsClient import BSClient

class Icon(TypedDict):
    id: int

class MemberData(TypedDict):
    icon: Icon
    tag: str
    name: str
    trophies: int
    role: str
    nameColor: str

class ClubData(TypedDict):
    tag: str
    name: str
    description: str
    trophies: int
    requiredTrophies: int
    members: list[MemberData]
    type: str
    badgeId: int

class BrawlerData(TypedDict):
      id: int
      rank: int
      trophies: int
      highestTrophies: int
      power: int
      starPowers: list[TypedDict('StarPower', name=str, id=int)]
      gadgets: list[TypedDict('Gadget', name=str, id=int)]
      gears: list[TypedDict('Gear', name=str, id=int, level=int)]
      name: str

class PlayerData(TypedDict):
    club: TypedDict('PlayerClubData', tag=str, name=str)
    isQualifiedFromChampionshipChallenge: bool
    _3vs3Victories: int # bruh can't start attribute with number
    icon: Icon
    tag: str
    name: str
    trophies: int
    expLevel: int
    expLevel: int
    expPoints: int
    highestTrophies: int
    powerPlayPoints: int
    highestPowerPlayPoints: int
    soloVictories: int
    duoVictories: int
    bestRoboRumbleTime: int
    bestTimeAsBigBrawler: int
    brawlers: list[BrawlerData]
    nameColor: str

@dataclass(unsafe_hash=True, eq=True, frozen=True)
class BattleProxy:
    battleTime: datetime = field(hash=True)
    trophyChange: int = field(hash=True)
    type: BattleType = field(hash=True)
    result: Result = field(hash=True)
    battle_data: dict = field(hash=False, compare=False, repr=False)
    
    def __eq__(self, other) -> bool:
        return (self.battle_data, self.trophyChange, self.type, self.result) == (other.battle_data, other.trophyChange, other.type, other.result)

class Poller:
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client: BSClient = bot.get_cog('BSClient')
    
    async def initialize_club(self, tag: str = None, club_data: ClubData = None) -> Club:
        if tag is club_data is None:
            raise ValueError('need club tag or club data')
        return await self.update_club(Club(tag or club_data['tag']), club_data, True, True)
        
    async def initialize_player(self, tag: str = None, member_data: Union[MemberData, PlayerData] = None, rank: int = None):
        if tag is member_data is None:
            raise ValueError('need player tag or player data')
        return await self.update_player(Player(tag or member_data['tag']), member_data, rank)
    
    async def update_club(self, club: Club, club_data: ClubData = None, update_players: bool = False, update_logs: bool = False) -> Club:
        if club_data is None:
            club_data = (await self.client.get_club(club.tag)).raw_data
            print(f"found {club_data['name']}({club.tag}), getting players")
        
        club.name = club_data['name']
        
        # players = {member_data['tag']: member_data for member_data in club_data['members']}

        if update_players:
            update_tasks = []
            init_tasks = []
            for i, member_data in enumerate(club_data['members']):
                if member_data['tag'] in club.members:
                    update_tasks.append(self.bot.loop.create_task(self.update_player(club.members[member_data['tag']], rank=i+1)))
                else:
                    init_tasks.append(self.initialize_player(member_data['tag'], rank=i+1))
            new_players: list[Player] = await asyncio.gather(*init_tasks)
            club.members.update({player.tag: player for player in new_players})
            await asyncio.gather(*update_tasks)

        if update_logs:
            battle_log_data: list[list[dict]] = list(map(lambda b: b.raw_data, await asyncio.gather(*[self.client.get_battle_logs(tag) for tag in club.members])))
            for tag, battle_log in zip(club.members, battle_log_data):
                club.members[tag].lastOnline = Poller.get_datetime(battle_log[0]['battleTime'])
            
            # battle_log_data = sum(map(lambda d: d.raw_data, await asyncio.gather(*[self.client.get_battle_logs(tag) for tag in club.members])), [])
            old_battles = club.battles.copy()
            unique_battles: set[BattleProxy] = club.battles
            for battle_data in sum(battle_log_data, []):
                if args := Poller.valid_battle(battle_data):
                    unique_battles.add(BattleProxy(*args, battle_data))
            new_battles = unique_battles - old_battles
            club.battles |= new_battles
            for battle_proxy in new_battles:
                new_battle = Battle(*[getattr(battle_proxy, v.name) for v in battle_proxy.__dataclass_fields__.values() if v.hash is not False]) # very sus and might break if dataclass updates
                try:
                    for team_member_data in (d for i in range(2) for d in battle_proxy.battle_data['battle']['teams'][i]):
                        new_battle.teams.append(team_member_data['tag'])
                        if player := club.members.get(team_member_data['tag']):
                            player.warBattles.append(new_battle)
                except KeyError:
                    assert True
        print(f"{club_data['name']}({club.tag}) initialized")
        return club
    
    async def update_player(self, player: Player, member_data: Union[MemberData, PlayerData] = None, rank: int = None) -> Player:
        if member_data is None:
            member_data: PlayerData = (await self.client.get_player(player.tag)).raw_data
        
        player.name = member_data['name']
        player.trophies = member_data['trophies']
        player.rank = rank
        
        return player
    
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
    