import os
from discord.ext import commands
from tokens import disc_token

class ClubBot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)
        self.guild_data = {}

bot = ClubBot(command_prefix='.')

@bot.event
async def on_ready():
    print('bot ready')

@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    print(f'unloaded {ext}')

@bot.command()
async def load(ctx, extension):
    bot.load_extension(ext := f'cogs.{extension}')
    print(f'loaded {ext}')

@bot.command()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(ext := f'cogs.{extension}')
    print(f'reloaded {ext}')

blacklist = []

for filename in os.listdir('./cogs'):
    if filename.endswith('.py') and not filename in blacklist:
        bot.load_extension(ext := f'cogs.{filename[:-3]}')
        print(f'loaded {ext}')

bot.run(disc_token)