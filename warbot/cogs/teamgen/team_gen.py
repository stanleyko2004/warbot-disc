from typing import NamedTuple
import random

from warbot.cogs.teamgen.stackedness import Player, Brawler
from warbot.cogs.teamgen.owners import OWNERS, OWNER_MAP

class OwnedPlayer(NamedTuple):
    tag: str
    score: int
    name: str
    brawlers: list[Brawler]
    owners: str

class Configuration(NamedTuple):
    s: list[OwnedPlayer]
    t: list[OwnedPlayer]
    i: list[OwnedPlayer]

def gen_configuration(players: list[Player], shuffle = False):  
    players = players.copy()
    if shuffle:
        random.shuffle(players)
    
    ownings = {o: [] for o in OWNERS}
    
    oplayers: list[OwnedPlayer] = []
    for p in players:
        if (owners := OWNER_MAP.get(p.tag)):
            oplayers.append(OwnedPlayer(*p, owners))
    oplayers.sort(key=lambda p: len(p.owners))
    
    for player in oplayers:
        shortest_owner = min(player.owners, key=lambda o: len(ownings[o]))
        ownings[shortest_owner].append(player)
    
    
    return Configuration(**ownings)