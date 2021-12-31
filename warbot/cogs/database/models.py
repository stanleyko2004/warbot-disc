from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.decl_api import DeclarativeMeta, registry

from datetime import datetime
import enum

mapper_registry = registry()

class Base(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = mapper_registry
    metadata = mapper_registry.metadata
    
    __init__ = mapper_registry.constructor

class Result(str, enum.Enum):
    victory = 'victory'
    draw = 'draw'
    defeat = 'defeat'
    
class BattleType(str, enum.Enum):
    soloRanked = 'soloRanked'
    teamRanked = 'teamRanked'

@mapper_registry.mapped
@dataclass
class Player:
    __tablename__ = 'player'

    __sa_dataclass_metadata_key__ = 'sa'
    tag: str = field(metadata={'sa': Column(String, primary_key=True)}) # treat as id
    name: str = field(default=None, metadata={'sa': Column(String)})
    trophies: int = field(default=None, metadata={'sa': Column(Integer)})
    lastOnline: datetime = field(default=None, metadata={'sa': Column(DateTime)})
    rank: int = field(default=None, metadata={'sa': Column(Integer)})
    warBattles: list[Battle] = field(default_factory=list, metadata={'sa': association_proxy('player_battles', 'battle')})


@mapper_registry.mapped
@dataclass
class Battle:
    __tablename__ = 'battle'
    
    __sa_dataclass_metadata_key__ = 'sa'
    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    time: datetime = field(default=None, metadata={'sa': Column(DateTime)})
    trophyChange: int = field(default=None, metadata={'sa': Column(Integer)})
    type: BattleType = field(default=None, metadata={'sa': Column(sqlalchemy.Enum(BattleType))})
    result: Result = field(default=None, metadata={'sa': Column(sqlalchemy.Enum(Result))})
    teams: list[Player] = field(default_factory=list, metadata={'sa': association_proxy('player_battles', 'player')})

@mapper_registry.mapped
class Player_Battle:
    __tablename__ = 'player_battle'
    
    playerTag: str = Column(ForeignKey('player.tag'), primary_key=True)
    battleId: int = Column(ForeignKey('battle.id'), primary_key=True)
    player: Player = relationship(Player, backref='player_battles')
    battle: Battle = relationship(Battle, backref='player_battles')
    
    def __init__(self, p1: Union[Player, Battle] = None, p2: Union[Player, Battle] = None):
        self.player = p1 if isinstance(p1, Player) else p2 if isinstance(p2, Player) else None
        self.battle = p1 if isinstance(p1, Battle) else p2 if isinstance(p2, Battle) else None

@mapper_registry.mapped
@dataclass
class Club:
    __tablename__ = 'club'
    
    __sa_dataclass_metadata_key__ = 'sa'
    tag: str = field(metadata={'sa': Column(String, primary_key=True)}) # treat as id
    name: str = field(default=None, metadata={'sa': Column(String)})
    trophies: int = field(default=None, metadata={'sa': Column(Integer)})
    wars: list[War] = field(default_factory=list, metadata={'sa': association_proxy('club_wars', 'war')})

@mapper_registry.mapped
@dataclass
class War:
    __tablename__ = 'war'

    __sa_dataclass_metadata_key__ = 'sa'
    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    clubs: list[Club] = field(default_factory=list, metadata={'sa': association_proxy('club_wars', 'club')})
    

@mapper_registry.mapped
class Club_War:
    __tablename__ = 'club_war'
    
    clubTag: str = Column(ForeignKey('club.tag'), primary_key=True)
    warId: int = Column(ForeignKey('war.id'), primary_key=True)
    club: Club = relationship(Club, backref='club_wars')
    war: War = relationship(War, backref='club_wars')
    
    def __init__(self, p1: Union[Club, War] = None, p2: Union[Club, War] = None):
        self.club = p1 if isinstance(p1, Club) else p2 if isinstance(p2, Club) else None
        self.war = p1 if isinstance(p1, War) else p2 if isinstance(p2, War) else None
