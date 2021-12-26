#ting the whole file
from datetime import datetime

from client import client
import asyncio

class Member:
  def __init__(self, member, rank):
    self.name = member['name'].encode("ascii", "ignore").decode() #emojis and stuff screw up spacing
    self.trophies = member['trophies']
    self.tag = member['tag']
    self.logs = {}
    self.rank = rank

class Battle:
  def __init__(self, battle):
    # if its a club league match in time range and not a power league match

    self.is_power_match = None #if none then its a power league match
    if 'type' in battle['battle']: #could be boss fight
      if battle['battle']['type'] == 'teamRanked': #team cl
        self.is_power_match = True
      elif (battle['battle']['type'] == 'soloRanked'): #solo cl
        self.is_power_match = False

    self.time = datetime.strptime(battle['battleTime'], '%Y%m%dT%H%M%S.%fZ') #datetime object
    self.in_time_range = (datetime.now() - self.time).total_seconds() < 24*3600 #boolean

    if ('trophyChange' in battle['battle']):
      self.trophies = battle['battle']['trophyChange'] #int
    else:
      self.trophies = None

    self.is_club_match = False if self.trophies == None else True

    self.is_current_club_match = self.in_time_range and self.is_club_match and self.is_power_match is not None

    #if fine then define attributes
    if self.is_current_club_match:
      self.result = battle['battle']['result'] #victory, draw, or defeat

      self.teams = []
      for i in range(2):
        for player in battle['battle']['teams'][i]:
          self.teams.append(player['tag'])

class ClubTable:

  def __init__(self, club_tag):
    self.club_tag = club_tag
    self.members = {}
    self.messages = []

  async def create(self):
    #repolling
    self.club = client.get_club(self.club_tag, use_cache=False)
    for member in self.club['members']:
      if not member['tag'] in self.members:
        self.members[str(member['tag'])] = Member(member, len(self.members)+1)
    await self.get_member_logs()

    #displaying the headers
    spacing = "{:<12} {:<6} {:<6} {:<6} {:<6} {:<6} {:<6} {:<6} {:<6} {:<11}"
    headers = ["Player", "t1", "t2", "t3", "t4", "gt1", "gt2", "gt3", "gt4", "last online"]
    self.messages.append(spacing.format(*headers) + '\n')

    #displaying the data
    for member_tag in self.members.keys():
      member = self.members[member_tag]
      args = [[str(member.rank) + '.' + member.name[:7]],[member.trophies],[member_tag]]
      for battle_time in member.logs.keys():
        battle = member.logs[battle_time]
        args[0].append(battle.result[:1].upper())
        args[1].append(battle.trophies)
        temp_mems = '' #mega sus
        for teammate_tag in battle.teams: #teammate is a player tag
          if teammate_tag != member_tag and teammate_tag in self.members:
            temp_mems += str(self.members[teammate_tag].rank) + ' '
        temp_mems.strip()
        if temp_mems == '':
          temp_mems = '~'
        args[2].append(temp_mems)
        if battle.is_power_match:
          for i in range(3):
            args[i].append('~')
      for i in range(3):
        args[i] += ['-'] * (9 - len(args[i])) #fix this? idk
      args[0].append('~' if member.last_online is None else member.last_online.strftime("%H:%M:%S"))
      args[1].append('~' if member.last_online is None else member.last_online.strftime("%m/%d/%Y"))
      args[2].append('-')
      message = ''''''
      for i in range(3):
        message += spacing.format(*args[i])+'\n'
      self.messages.append(message)
    return self.messages

  async def get_member_logs(self):
    for member_tag in self.members.keys():
      member = self.members[member_tag]
      await asyncio.sleep(0.1) #prevent rate limit?
      logs = client.get_battle_logs(member_tag).raw_data
      if len(logs) > 0: #in case log wipes
        member.last_online = datetime.strptime(logs[0]['battleTime'], '%Y%m%dT%H%M%S.%fZ')
        for battle in logs:
          new_battle = Battle(battle)
          if new_battle.is_current_club_match and not any(i.time == new_battle.time for i in member.logs): #new club match
            member.logs[new_battle.time] = new_battle
      else:
        member.last_online = None


if __name__ == "__main__":
  async def main():
    table = ClubTable('#2PLUPQPV')
    print(await table.create())

    # logs = client.get_battle_logs('#8LVLYLJU').raw_data
    # pass
    # await asyncio.sleep(10)
    # await table.create() #testing that battles don't overlap

  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())