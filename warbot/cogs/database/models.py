from __future__ import annotations
from dataclasses import dataclass, field

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.decl_api import DeclarativeMeta, registry

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
    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    
    # store days
    days: list[Day] = field(default_factory=list, metadata={'sa': relationship('Day')})

@mapper_registry.mapped
@dataclass
class Club:
    __tablename__ = 'club'

    __sa_dataclass_metadata_key__ = 'sa'
    tag: str = field(metadata={'sa': Column(String, primary_key=True)}) # treat as id
    
    #access days

@mapper_registry.mapped
@dataclass
class Day:
    __tablename__ = 'day'

    __sa_dataclass_metadata_key__ = 'sa'
    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})

    # store war
    warId: str = field(init=False, metadata={'sa': Column(ForeignKey('war.id'))})

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
    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    
    # club_war_day association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    dayId: int = field(init=False, metadata={'sa': Column(ForeignKey('day.id'), primary_key=True)})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId', 'dayId'],
                                           ['club_war_day.clubTag', 'club_war_day.warId', 'club_war_day.dayId']),)

@mapper_registry.mapped
@dataclass
class Club_War:
    """Snapshot of club during a specific war"""
    __tablename__ = 'club_war'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    war: War = field(default=None, metadata={'sa': relationship(War, backref='club_wars')})
    club: Club = field(default=None, metadata={'sa': relationship(Club, backref='club_wars')})

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
    
    club_war: Club_War = field(default=None, metadata={'sa': relationship(Club_War, backref='club_war_players')})
    player: Player = field(default=None, metadata={'sa': relationship(Player, backref='club_war_players')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId'],
                                           ['club_war.clubTag', 'club_war.warId']),)

@mapper_registry.mapped
@dataclass
class Club_War_Day:
    __tablename__ = 'club_war_day'

    __sa_dataclass_metadata_key__ = 'sa'
    
    # club-war-day association
    clubTag: str = field(init=False, metadata={'sa': Column(ForeignKey('club.tag'), primary_key=True)})
    warId: int = field(init=False, metadata={'sa': Column(ForeignKey('war.id'), primary_key=True)})
    dayId: int = field(init=False, metadata={'sa': Column(ForeignKey('day.id'), primary_key=True)})

    club_war: Club_War = field(default=None, metadata={'sa': relationship(Club_War, backref='club_war_days')})
    day: Day = field(default=None, metadata={'sa': relationship(Day, backref='club_war_days')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId'],
                                           ['club_war.clubTag', 'club_war.warId']),)
    
    # actual data
    battles: set[Battle] = field(default_factory=set, metadata={'sa': relationship(Battle, collection_class=set)})
    club_war_day_players: list[Club_War_Day_Player] = field(default_factory=list, metadata={'sa': relationship('Club_War_Day_Player', back_populates='club_war_day')})
    
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
    
    club_war_day: Club_War_Day = field(default=None, metadata={'sa': relationship(Club_War_Day, back_populates='club_war_day_players')})
    player: Club_War_Player = field(default=None, metadata={'sa': relationship(Club_War_Player, backref='club_war_day_players')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId', 'dayId'],
                                           ['club_war_day.clubTag', 'club_war_day.warId', 'club_war_day.dayId']),
                      ForeignKeyConstraint(['clubTag', 'warId', 'playerTag'],
                                           ['club_war_player.clubTag','club_war_player.warId','club_war_player.playerTag']))
    
    # actual data
    battles: list[Battle] = field(default_factory=list, metadata={'sa': association_proxy('club_war_day_player_battles', 'battle')})

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
    
    club_war_day_player: Club_War_Day_Player = field(default=None, metadata={'sa': relationship(Club_War_Day_Player, backref='club_war_day_player_battles')})
    battle: Battle = field(default=None, metadata={'sa': relationship(Battle, backref='club_war_day_player_battles')})
    __table_args__ = (ForeignKeyConstraint(['clubTag', 'warId', 'dayId', 'playerTag'],
                                           ['club_war_day_player.clubTag', 'club_war_day_player.warId', 'club_war_day_player.dayId', 'club_war_day_player.playerTag']),)
    
    # actual data
    isGolden: bool = field(default=None, metadata={'sa': Column(Boolean)})