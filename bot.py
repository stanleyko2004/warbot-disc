import os
import discord
from discord.ext import commands

client = commands.Bot(command_prefix='.')

@client.event
async def on_ready():
    print('bot ready')

@client.command()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(ext := f'cogs.{extension}')
    print(f'reloaded {ext}')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(ext := f'cogs.{filename[:-3]}')
        print(f'loaded {ext}')

client.run('OTIyMzUxNzE5MTk3ODM1MzM0.YcAM-g.dzubbI2ePsAOZ4rZ1tX6x2I5i3Q')