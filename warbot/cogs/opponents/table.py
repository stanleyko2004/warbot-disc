from .models import Club, BattleType

spacing = "{:<12} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<8}"
headers = ["Player", "t1", "t2", "t3", "t4", "g1", "g2", "g3", "g4", "online"]

def generate_message(club: Club) -> str:
    message: str = ''
    message += spacing.format(*headers) + '\n'
    for member in club.members.values():
        args: list[str] = []
        args.append(f'{str(member.rank)}.{disc_safe(member.name)[:7]}') # ,[member.trophies],[tag]]
        for battle in member.warBattles:
            args.append(battle.result[:1].upper() + str(battle.trophyChange))
            # args[0].append(battle.result[:1].upper())
            # args[1].append(battle.trophyChange)
            # temp_mems = '' #mega sus
            # for teammate_tag in battle.teams: #teammate is a player tag
            #     if teammate_tag != tag and teammate_tag in club.members:
            #         temp_mems += str(club.members[teammate_tag].rank) + ' '
            # temp_mems.strip()
            # if temp_mems == '':
            #     temp_mems = '~'
            # args[2].append(temp_mems)
            if battle.type == BattleType.TEAM:
                args.append('~')
        # for i in range(3):
        #     args[i] += ['-'] * (9 - len(args[i])) #fix this? idk
        args += ['-'] * (9 - len(args))
        # args[0].append('~' if member.lastOnline is None else member.lastOnline.strftime("%H:%M:%S"))
        # args[1].append('~' if member.lastOnline is None else member.lastOnline.strftime("%m/%d/%Y"))
        # args[2].append('-')
        # message = ''''''
        args.append('~' if member.lastOnline is None else member.lastOnline.strftime("%H:%M"))
        # for i in range(3):
        #   message += spacing.format(*args[i])+'\n'
        # messages.append(message)
        message += spacing.format(*args)+'\n'
    return f'```{message}```'

def disc_safe(str: str) -> str:
    return str.encode("ascii", "ignore").decode()