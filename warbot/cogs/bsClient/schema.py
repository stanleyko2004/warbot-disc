from __future__ import annotations
from typing import TypedDict

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

class BattleData(TypedDict):
    battleTime: str
    event: dict[str]
    battle: _InnerBattleData

class _InnerBattleData(TypedDict):
    mode: str
    type: str
    result: str
    duration: int
    trophyChange: int
    starPlayer: _Battler
    teams: list[list[_Battler]]

class _Battler(TypedDict):
    tag: str
    name: str
    brawler: str