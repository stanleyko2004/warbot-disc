from .models import Club, BattleType

spacing = "{:<12} {:<6} {:<6} {:<6} {:<6} {:<6} {:<6} {:<6} {:<6} {:<11}"
headers = ["Player", "t1", "t2", "t3", "t4", "gt1", "gt2", "gt3", "gt4", "last online"]

def generate_messages(club: Club) -> list[str]:
    messages = []
    messages.append(spacing.format(*headers) + '\n')
    for tag, member in club.members.items():
        args = [[str(member.rank) + '.' + disc_safe(member.name)[:7]],[member.trophies],[tag]]
        for battle in member.warBattles:
            args[0].append(battle.result[:1].upper())
            args[1].append(battle.trophyChange)
            temp_mems = '' #mega sus
            for teammate_tag in battle.teams: #teammate is a player tag
                if teammate_tag != tag and teammate_tag in club.members:
                    temp_mems += str(club.members[teammate_tag].rank) + ' '
            temp_mems.strip()
            if temp_mems == '':
                temp_mems = '~'
            args[2].append(temp_mems)
            if battle.type == BattleType.TEAM:
                for i in range(3):
                    args[i].append('~')
        for i in range(3):
            args[i] += ['-'] * (9 - len(args[i])) #fix this? idk
        args[0].append('~' if member.lastOnline is None else member.lastOnline.strftime("%H:%M:%S"))
        args[1].append('~' if member.lastOnline is None else member.lastOnline.strftime("%m/%d/%Y"))
        args[2].append('-')
        message = ''''''
        for i in range(3):
          message += spacing.format(*args[i])+'\n'
        messages.append(message)
    return messages

def disc_safe(str):
    return str.encode("ascii", "ignore").decode()