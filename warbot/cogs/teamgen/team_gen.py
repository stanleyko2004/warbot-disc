from typing import NamedTuple
import random

from warbot.cogs.teamgen.stackedness import Player, Brawler
from warbot.cogs.teamgen.owners import OWNERS, OWNER_MAP
from warbot.cogs.teamgen.kernel import NUMBRAWLERS

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
    
    if len(oplayers) % 3 == 1: # add in 2 randoms
        last_player = oplayers.pop()
        oplayers += [OwnedPlayer('#', 0, 'random', [Brawler('',0,0,0)]*NUMBRAWLERS, OWNERS), last_player, OwnedPlayer('#', 0, 'random', [Brawler('',0,0,0)]*NUMBRAWLERS, OWNERS)]
    elif len(oplayers) % 3 == 2: # add in 1 random
        oplayers.append(OwnedPlayer('#', 0, 'random', [Brawler('',0,0,0)]*NUMBRAWLERS, OWNERS))
    
    for player in oplayers:
        shortest_owner = min(player.owners, key=lambda o: len(ownings[o]))
        ownings[shortest_owner].append(player)
    
    
    return Configuration(**ownings)