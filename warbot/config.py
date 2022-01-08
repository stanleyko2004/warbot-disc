import os
from sqlalchemy import create_engine
from util import WarSchedule
import datetime

COMMAND_PREFIX = '.'

def BS_TOKEN():
    return os.getenv('BS_TOKEN')

def DISC_TOKEN():
    return os.getenv('DISC_TOKEN')

# DB_ENGINE = create_engine('sqlite:///warbot.db')
DB_ENGINE = create_engine('sqlite://')

PST = datetime.timezone(datetime.timedelta(hours=-8))
MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

WAR_SCHEDULE = WarSchedule(WED, datetime.time(1, tzinfo=PST))