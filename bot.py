import os
from discord.ext import commands
from dotenv import load_dotenv
from warbot.config import COMMAND_PREFIX, DISC_TOKEN

# print(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv()

class ClubBot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)
        self.guild_data = {}

bot = ClubBot(command_prefix=COMMAND_PREFIX)

@bot.event
async def on_ready():
    print('bot ready')

@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(ext := f'warbot.cogs.{extension}')
    print(f'unloaded {ext}')

@bot.command()
async def load(ctx, extension):
    bot.load_extension(ext := f'warbot.cogs.{extension}')
    print(f'loaded {ext}')

@bot.command()
async def reload(ctx, extension):
    # bot.unload_extension(f'cogs.{extension}')
    # bot.load_extension(ext := f'cogs.{extension}')
    bot.reload_extension(ext := f'warbot.cogs.{extension}')
    print(f'reloaded {ext}')

# blacklist = {}#'__init__.py', 'addOpponents.py', 'monitoring.py', 'deleteOpponents.py'}

# for filename in os.listdir('./warbot/cogs'):
#     if filename.endswith('.py') and not filename in blacklist:
#         bot.load_extension(ext := f'warbot.cogs.{filename[:-3]}')
#         print(f'loaded {ext}')

# bot.load_extension('warbot.cogs.addOpponents')
# bot.load_extension('warbot.cogs.monitoring')
# bot.load_extension('warbot.cogs.deleteOpponents')

bot.load_extension('warbot.cogs.bsClient')
bot.load_extension('warbot.cogs.opponents')
bot.load_extension('warbot.cogs.database')
bot.load_extension('warbot.cogs.teamgen')


bot.run(DISC_TOKEN())