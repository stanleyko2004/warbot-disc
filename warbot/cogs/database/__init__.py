from discord.ext import commands
from sqlalchemy.orm import sessionmaker
from warbot.config import DB_ENGINE
from .models import mapper_registry

mapper_registry.metadata.create_all(DB_ENGINE)

class DBSession(sessionmaker, commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        sessionmaker.__init__(self, bind=DB_ENGINE)

def setup(bot: commands.Bot):
    bot.add_cog(DBSession(bot))