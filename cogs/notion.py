from discord import app_commands
from discord.ext import commands
import discord
import os



class Notion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def fuga(self, ctx):
        await ctx.send("テスト成功！")

async def setup(bot):
    if os.path.isfile('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    MY_GUILD = discord.Object(id=int(os.environ['DISCORD_GUILD_ID']))
    # await bot.add_cog(Notion(bot)) 
    await bot.add_cog(Notion(bot), guilds=MY_GUILD) 