import discord
from discord.ext import commands
from discord import app_commands

from discord.ext.commands import Greedy, Context
from typing import Literal, Optional

import os
import traceback

cogslist = [
    'cogs.notion_manager'
]

class o_o(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='/',
            intents=discord.Intents.all())
        if os.path.isfile('.env'):
            from dotenv import load_dotenv
            load_dotenv()
        self.MY_GUILD = discord.Object(id=int(os.environ['DISCORD_GUILD_ID']))

    async def setup_hook(self):
        for cog in cogslist:
            try: 
                await self.load_extension(cog)
            except Exception:
                traceback.print_exc()

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(f'豊かな人生'))
        await self.tree.sync()
        await self.tree.sync(guild=self.MY_GUILD)

bot = o_o()

@bot.tree.command(name='reload')
async def reload(interaction: discord.Interaction):
    print('reloading...')
    for cog in cogslist:
        try: 
            await bot.reload_extension(cog)
        except Exception:
            traceback.print_exc()
    await interaction.response.send_message('reloading success!')

bot.run(os.environ['DISCORD_BOT_TOKEN'])        

