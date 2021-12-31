import os
from sqlalchemy import create_engine

COMMAND_PREFIX = '.'

def BS_TOKEN():
    return os.getenv('BS_TOKEN')

def DISC_TOKEN():
    return os.getenv('DISC_TOKEN')

DB_ENGINE = create_engine('sqlite:///warbot.db')