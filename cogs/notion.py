from discord import app_commands
from discord.ext import commands
import discord
import os
import requests

class Notion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command()
    async def inbox(self, interaction: discord.Interaction, title: str) -> None:
        url = "https://api.notion.com/v1/pages"

        NOTION_API_KEY = os.environ['NOTION_API_KEY']
        NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
        emoji = "😐"
        headers = {
            "Accept": "application/json",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + NOTION_API_KEY,
        }

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "icon": {"emoji": emoji},
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {"content": title},
                        }
                    ],
                },
            },
        }

        response = requests.post(url, json=payload, headers=headers)
        result_dict = response.json()
        result = result_dict["object"]
        page_url = result_dict["url"]
        page_title = result_dict["properties"]["Name"]["title"][0]["text"]["content"]

        message = ""
        if result == "page":
            message = "「" + page_title + "」が作成されたよ～ XXXX!!\n " + page_url
        elif result == "error":
            message = "なんかエラーが発生しているみたい！\n " + page_url
        else:
            message = ("例外起きて草。なんも分からん。\n " + page_url,)

        await interaction.response.send_message(message)

async def setup(bot: commands.Bot) -> None:
    MY_GUILD = discord.Object(id=int(os.environ['DISCORD_GUILD_ID']))
    await bot.add_cog(Notion(bot), guild=MY_GUILD) 