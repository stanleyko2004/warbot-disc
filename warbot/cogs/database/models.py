from __future__ import annotations
from dataclasses import dataclass, field

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.decl_api import DeclarativeMeta, registry
from sqlalchemy.orm.collections import attribute_mapped_collection

from datetime import datetime
import enum

from sqlalchemy.sql.schema import ForeignKeyConstraint

mapper_registry = registry()

class Result(str, enum.Enum):
    victory = 'victory'
    draw = 'draw'
    defeat = 'defeat'

class BattleType(str, enum.Enum):
    soloRanked = 'soloRanked'
    teamRanked = 'teamRanked'

@mapper_registry.mapped
@dataclass
class War:
    __tablename__ = 'war'
    
    __sa_dataclass_metadata_key__ = 'sa'
    id: int = field(init=False, repr=False, metadata={'sa': Column(Integer, primary_key=True, autoincrement=True)})
    start: datetime = field(metadata={'sa': Column(DateTime)})
    
    # store days
    days: list[Day] = field(default_factory=list, repr=False, metadata={'sa': relationship('Day')})
    club_wars: list[Club_War] = field(default_factory=list, repr=False, metadata={'sa': relationship('Club_War', back_populates='war')})

    def add_day(self, day: Day) -> Day:
        self.days.append(day)
        for club_war in self.club_wars:
            Club_War_Day(club_war=club_war, day=day)
        return day
    
    def add_club(self, club: Club) -> Club_War:
        club_war = Club_War(war=self, club=club)
        for day in self.days:
            # club_war.club_war_days[day.start] = Club_War_Day(day=day)
            
            Club_War_Day(club_war=club_war, day=day)
            assert club_war
        return club_war

@mapper_registry.mapped
@dataclass
class Club:
    __tablename__ = 'club'

    __sa_dataclass_metadata_key__ = 'sa'
    tag: str = field(metadata={'sa': Column(String, primary_key=True)}) # treat as id
    

@mapper_registry.mapped
@dataclass
class Day:
    __tablename__ = 'day'

    __sa_dataclass_metadata_key__ = 'sa'
    id: int = field(init=False, repr=False, metadata={'sa': Column(Integer, primary_key=True, autoincrement=True)})
    start: datetime = field(metadata={'sa': Column(DateTime)})
    
    # store war
    warId: str = field(init=False, repr=False, metadata={'sa': Column(ForeignKey('war.id'))})

@mapper_registry.mapped
@dataclass
class Player:
    __tablename__ = 'player'

    __sa_dataclass_metadata_key__ = 'sa'
    tag: str = field(metadata={'sa': Column(String, primary_key=True)}) # treat as id

@mapper_registry.mapped
@dataclass
class Battle:
    __tablename__ = 'battle'

    __sa_dataclass_metadata_key__ = 'sa'
    id: int = field(init=False, repr=False, metadata={'sa': Column(Integer, primary_key=True, autoincrement=True)})
    
    # club_war_day association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'))})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'))})
    dayId: int = field(init=False, metadata={'sa': Column(ForeignKey('day.id'))})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId', 'dayId'],
                                           ['club_war_day.clubTag', 'club_war_day.warId', 'club_war_day.dayId']),)

    club_war: Club_War = field(init=False, repr=False, metadata={'sa': relationship('Club_War')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId'],
                                           ['club_war.clubTag', 'club_war.warId']),
                      ForeignKeyConstraint(['clubTag', 'warId', 'dayId'],
                                           ['club_war_day.clubTag', 'club_war_day.warId', 'club_war_day.dayId']))
    
    club_war_day_player_battles: dict[str, Club_War_Day_Player_Battle] = field(init=False, repr=False, 
                                                                          metadata={'sa': relationship('Club_War_Day_Player_Battle',
                                                                                                       back_populates='battle',
                                                                                                       collection_class=attribute_mapped_collection('playerTag'))})
    battleTime: datetime = field(metadata={'sa': Column(DateTime)})
    type: BattleType = field(metadata={'sa': Column(Enum(BattleType))})
    result: Result = field(metadata={'sa': Column(Enum(Result))})
    trophyChange: int = field(metadata={'sa': Column(Integer)})
    starPlayerTag: str = field(metadata={'sa': Column(String)}) # in order to uniquely identify battle
    
    def add_player(self, club_war_day_player: Club_War_Day_Player) -> Club_War_Day_Player_Battle:
        club_war_day_player_battle = Club_War_Day_Player_Battle(club_war_day_player=club_war_day_player)
        # club_war_day_player_battle.
        self.club_war_day_player_battles[club_war_day_player.player_tag] = club_war_day_player_battle
        return club_war_day_player_battle
    
@mapper_registry.mapped
@dataclass
class Club_War:
    """Snapshot of club during a specific war"""
    __tablename__ = 'club_war'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war association
    clubTag: str = field(init=False, repr=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, repr=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    war: War = field(default=None, metadata={'sa': relationship(War, back_populates='club_wars')})
    club: Club = field(default=None, metadata={'sa': relationship(Club, backref='club_wars')})

    club_war_players: dict[str, Club_War_Player] = field(init=False, repr=False, 
                                                         metadata={'sa': relationship('Club_War_Player',
                                                                                      back_populates='club_war',
                                                                                      collection_class=attribute_mapped_collection('player_tag'))})
    
    club_war_days: dict[datetime, Club_War_Day] = field(init=False, repr=False, metadata={'sa': relationship('Club_War_Day',
                                                                                back_populates='club_war',
                                                                                collection_class=attribute_mapped_collection('day_start'))})

    name: str = field(init=False, repr=False, metadata={'sa': Column(String)})
    trophies: int = field(init=False, repr=False, metadata={'sa': Column(Integer)})
    
    def add_player(self, player: Player) -> Club_War_Player:
        club_war_player = Club_War_Player(player=player)
        self.club_war_players[player.tag] = club_war_player
        for club_war_day in self.club_war_days.values():
            Club_War_Day_Player(club_war_day=club_war_day, player=club_war_player)
        return club_war_player

@mapper_registry.mapped
@dataclass
class Club_War_Player:
    """Snapshot of player in a specific club_war"""
    __tablename__ = 'club_war_player'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war-player association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    playerTag: str = field(init=False, metadata={'sa': Column(ForeignKey('player.tag'), primary_key=True)})
    
    player: Player = field(default=None, metadata={'sa': relationship(Player, backref='club_war_players')})
    club_war: Club_War = field(default=None, metadata={'sa': relationship(Club_War, back_populates='club_war_players')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId'],
                                           ['club_war.clubTag', 'club_war.warId']),)
    
    name: str = field(init=False, repr=False, metadata={'sa': Column(String)})
    trophies: int = field(init=False, repr=False, metadata={'sa': Column(Integer)})
    lastOnline: datetime = field(init=False, repr=False, metadata={'sa': Column(DateTime)})
    rank: int = field(init=False, repr=False, metadata={'sa': Column(Integer)})
    
    @property
    def player_tag(self): # primary keys don't get set until the object is in the databas so need this to access player tag
        return self.player.tag

@mapper_registry.mapped
@dataclass
class Club_War_Day:
    __tablename__ = 'club_war_day'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war-day association
    clubTag: str = field(init=False, repr=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, repr=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    dayId: int = field(init=False, repr=False, metadata={'sa': Column(ForeignKey('day.id'), primary_key=True)})

    day: Day = field(default=None, metadata={'sa': relationship(Day, backref='club_war_days')})
    club_war: Club_War = field(default=None, metadata={'sa': relationship(Club_War, back_populates='club_war_days')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId'],
                                           ['club_war.clubTag', 'club_war.warId']),)
    
    # actual data
    club_war_day_players: dict[str, Club_War_Day_Player] = field(init=False, repr=False, 
                                                            metadata={'sa': relationship('Club_War_Day_Player', 
                                                                                         back_populates='club_war_day',
                                                                                         collection_class=attribute_mapped_collection('player_tag'))})
    
    clubTrophies: int = field(init=False, default=0, repr=False, metadata={'sa': Column(Integer)})
    redTicketsUsed: int = field(init=False, default=0, repr=False, metadata={'sa': Column(Integer)})
    goldenTicketsUsed: int = field(init=False, default=0, repr=False, metadata={'sa': Column(Integer)})
    
    @property
    def day_start(self):
        return self.day.start
    
    @property
    def club_trophies(self):
        return sum(b.trophyChange for b in self.battles)
    
@mapper_registry.mapped
@dataclass
class Club_War_Day_Player:
    __tablename__ = 'club_war_day_player'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war-day-player association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    dayId: int = field(init=False, metadata={'sa': Column(ForeignKey('day.id'), primary_key=True)})
    playerTag: str = field(init=False, metadata={'sa': Column(ForeignKey('player.tag'), primary_key=True)})
    
    player: Club_War_Player = field(default=None, metadata={'sa': relationship(Club_War_Player, backref='club_war_day_players')})
    club_war_day: Club_War_Day = field(default=None, metadata={'sa': relationship(Club_War_Day, back_populates='club_war_day_players')})
    club_war_day_player_battles: list[Club_War_Day_Player_Battle] = field(init=False, repr=False, 
                                                                    metadata={'sa': relationship('Club_War_Day_Player_Battle',
                                                                                                 back_populates='club_war_day_player')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId', 'dayId'],
                                           ['club_war_day.clubTag', 'club_war_day.warId', 'club_war_day.dayId']),
                      ForeignKeyConstraint(['clubTag', 'warId', 'playerTag'],
                                           ['club_war_player.clubTag','club_war_player.warId','club_war_player.playerTag']))
    
    # actual data
    battles: list[Battle] = field(init=False, repr=False, metadata={'sa': association_proxy('club_war_day_player_battles', 'battle')})

    @property
    def player_tag(self): # primary keys don't get set until the object is in the databas so need this to access player tag
        return self.player.player.tag
    
@mapper_registry.mapped
@dataclass
class Club_War_Day_Player_Battle:
    __tablename__ = 'club_war_day_player_battle'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war-day-player association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    dayId: int = field(init=False, metadata={'sa': Column(ForeignKey('day.id'), primary_key=True)})
    playerTag: str = field(init=False, metadata={'sa': Column(ForeignKey('player.tag'), primary_key=True)})
    battleId: str = field(init=False, metadata={'sa': Column(ForeignKey('battle.id'), primary_key=True)})
    
    club_war_day_player: Club_War_Day_Player = field(default=None, metadata={'sa': relationship(Club_War_Day_Player, back_populates='club_war_day_player_battles')})
    
    battle: Battle = field(default=None, metadata={'sa': relationship(Battle, back_populates='club_war_day_player_battles')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId', 'dayId', 'playerTag'],
                                           ['club_war_day_player.clubTag', 'club_war_day_player.warId', 'club_war_day_player.dayId', 'club_war_day_player.playerTag']),)
    
    # actual data
    isGolden: bool = field(default=None, metadata={'sa': Column(Boolean)})
    
    @property
    def player_tag(self): # primary keys don't get set until the object is in the databas so need this to access player tag
        return self.club_war_day_player.player.player.tag