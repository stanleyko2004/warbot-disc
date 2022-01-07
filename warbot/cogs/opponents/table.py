from .models import Club, BattleType, Player

spacing = "{:<12} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<3} {:<12}"
headers = ["Player", "t1", "t2", "t3", "t4", "g1", "g2", "g3", "g4", "tot", "last online"]

def generate_message(club: Club) -> str:
    message: str = ''
    message += spacing.format(*headers) + '\n'
    sorted_by_last_online: list[Player] = list(club.members.values())
    sorted_by_last_online.sort(key=lambda x:x.lastOnline, reverse=True)
    total_trophies: int = 0
    for member in sorted_by_last_online:
        args: list[str] = []
        args.append(f'{str(member.rank)}.{disc_safe(member.name)[:7]}') # ,[member.trophies],[tag]]
        member_trophies: int = 0
        for battle in member.warBattles:
            args.append(battle.result[:1].upper() + str(battle.trophyChange))
            member_trophies += battle.trophyChange
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
        total_trophies += member_trophies
        # for i in range(3):
        #     args[i] += ['-'] * (9 - len(args[i])) #fix this? idk
        args += ['-'] * (9 - len(args))
        args.append(str(member_trophies))
        # args[0].append('~' if member.lastOnline is None else member.lastOnline.strftime("%H:%M:%S"))
        # args[1].append('~' if member.lastOnline is None else member.lastOnline.strftime("%m/%d/%Y"))
        # args[2].append('-')
        # message = ''''''
        args.append('~' if member.lastOnline is None else member.lastOnline.strftime("%H:%M %m/%d"))
        # for i in range(3):
        #   message += spacing.format(*args[i])+'\n'
        # messages.append(message)
        message += spacing.format(*args)+'\n'
    message += f'\nTotal Trophies: {total_trophies}'
    return f'```{message}```'

def disc_safe(str: str) -> str:
    return str.encode("ascii", "ignore").decode()