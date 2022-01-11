from .models import Club, BattleType, Player
from warbot.cogs.database.models import Club_War, Club_War_Day

spacing = "{:<12} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<2} {:<3} {:<12}"
headers = ["Player", "t1", "t2", "t3", "t4", "g1", "g2", "g3", "g4", "tot", "last online"]

def generate_message(club_war_day: Club_War_Day) -> str:
    message: str = ''
    message += spacing.format(*headers) + '\n'
    club_war_day_players = sorted(club_war_day.club_war_day_players.values(), key=lambda p:p.player.lastOnline, reverse=True)
    for club_war_day_player in club_war_day_players:
        args: list[str] = []
        args.append(f'{str(club_war_day_player.player.rank)}.{disc_safe(club_war_day_player.player.name)[:7]}') # ,[member.trophies],[tag]]
        for battle in club_war_day_player.battles:
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
        args.append(str(club_war_day_player.total_trophies))
        # args[0].append('~' if member.lastOnline is None else member.lastOnline.strftime("%H:%M:%S"))
        # args[1].append('~' if member.lastOnline is None else member.lastOnline.strftime("%m/%d/%Y"))
        # args[2].append('-')
        # message = ''''''
        lastOnline = club_war_day_player.player.lastOnline
        args.append('~' if lastOnline is None else lastOnline.strftime("%H:%M %m/%d"))
        # for i in range(3):
        #   message += spacing.format(*args[i])+'\n'
        # messages.append(message)
        message += spacing.format(*args)+'\n'
    message += f'\nTotal Trophies: {club_war_day.club_trophies}'
    reds, goldens = club_war_day.tickets_used
    message += f'\nRed tickets used: {reds}  Golden tickets used: {goldens}'
    return f'```{message}```'

def disc_safe(str: str) -> str:
    return str.encode("ascii", "ignore").decode()