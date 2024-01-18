from typing import NamedTuple
from warbot.cogs.teamgen.scoring import GOOD

BID_OFFSET = 16000000

class Brawler(NamedTuple):
    name: str
    power: int
    score: int
    id: int

class Player(NamedTuple):
    tag: str
    score: int
    name: str
    brawlers: list[Brawler]

def good_brawler(brawler):
    if brawler['power'] < 9:
        return False
    bname = brawler['name'].lower()
    bid = brawler['id'] - BID_OFFSET
    if brawler['power'] > 9:
        return Brawler(bname, brawler['power'], GOOD.get(bname, (None,None,0))[2] + brawler['power'] - 9, bid)
        return bname, brawler['power'], GOOD.get(bname, (None,None,0))[2] + brawler['power'] - 9
    if bname not in GOOD:
        return False
    sps = [s['name'].lower() for s in brawler['starPowers']]
    if sps:
        sps.append(True)
    sps.append(False)
    gts = [g['name'].lower() for g in brawler['gadgets']]
    if gts:
        gts.append(True)
    gts.append(False)
    
    if GOOD[bname][0] not in sps or GOOD[bname][1] not in gts:
        return False

    return Brawler(bname, 9, GOOD[bname][2], bid)

async def check_player(session, tag) -> Player:
    t = await session.get_player(tag)
    g = [good_brawler(b) for b in t['brawlers'] if good_brawler(b)]
    g.sort(key=lambda b: (b.power, -list(GOOD).index(b.name) if b.name in GOOD else float('-inf')), reverse=True)
    score = sum([b.score for b in g])
    return Player(tag, score, t['name'], g)