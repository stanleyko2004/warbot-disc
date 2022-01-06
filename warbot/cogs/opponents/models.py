from __future__ import annotations
from dataclasses import dataclass, fields, field
from abc import ABC
from enum import Enum

import json
from datetime import datetime

@dataclass
class StoredObject(ABC):
    
    def tojson(self):
        asdict = dict((field.name, getattr(self, field.name)) for field in fields(self))
        return json.dumps(asdict, indent=4, default=self.serialize)
    
    def serialize(obj):
        pass

class Result(str, Enum):
    VICTORY = 'victory'
    DRAW = 'draw'
    DEFEAT = 'defeat'
    
class BattleType(str, Enum):
    SOLO = 'soloRanked'
    TEAM = 'teamRanked'

@dataclass(init=True)
class Player(StoredObject):
    tag: str = ''
    name: str = ''
    trophies: int = 0
    warBattles: list[Battle] = field(default_factory=list)
    lastOnline: datetime = None
    rank: int = None

@dataclass(init=True)
class Battle(StoredObject):
    time: datetime = None
    trophyChange: int = 0
    type: BattleType = None
    result: Result = None
    teams: list[str] = field(default_factory=list)
    

@dataclass(init=True)
class Club(StoredObject):
    tag: str = ''
    name: str = ''
    members: dict[str, Player] = field(default_factory=dict)
    battles: set = field(default_factory=set)