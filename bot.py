import os
from discord.ext import commands
from tokens import disc_token

class ClubBot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)
        self.guild_data = {}

client = ClubBot(command_prefix='.')

@client.event
async def on_ready():
    print('bot ready')

@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(f'unloaded {ext}')

@client.command()
async def load(ctx, extension):
    client.load_extension(ext := f'cogs.{extension}')
    print(f'loaded {ext}')

@client.command()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(ext := f'cogs.{extension}')
    print(f'reloaded {ext}')

blacklist = ['monitoring.py']

for filename in os.listdir('./cogs'):
    if filename.endswith('.py') and not filename in blacklist:
        client.load_extension(ext := f'cogs.{filename[:-3]}')
        print(f'loaded {ext}')

client.run(disc_token)