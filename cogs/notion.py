from discord import app_commands
from discord.ext import commands
import discord
import os
import requests
import json

class Notion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):       
        # Notion setup
        self.NOTION_API_KEY = os.environ['NOTION_API_KEY']
        self.NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
        self.NOTION_API_URL = "https://api.notion.com/v1/pages"

        # Discord setup
        self.DISCORD_INBOX_CHANNEL = self.bot.get_channel(int(os.environ['DISCORD_INBOX_CHANNEL_ID']))

    def post_inbox(self, title: str, content='', url='', emoji='😐') -> str:
        headers = {
            "Accept": "application/json",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.NOTION_API_KEY,
        }

        payload = {
            "parent": {"database_id": self.NOTION_DATABASE_ID},
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
            
            "children":[
            {
                "object": 'block',
                "type": "bookmark",
                "bookmark": {
                    "url": url
                }
            },]
    #         "children":[
    #             {
    #                 "rich_text": [
    #                         {
    #                              "text": {
    #                                 "content": content,
    #                                 "link": url
    #                                 }}
    #                             ],
    #             },       
    #    ],
        }

        response = requests.post(self.NOTION_API_URL, json=payload, headers=headers)
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

        return message

    @app_commands.command()
    async def inbox(self, interaction: discord.Interaction, title: str) -> None:
        message = self.post_inbox(title)
        await interaction.response.send_message(message)

    @commands.Cog.listener(name='on_message')
    async def good_reaction(self, message: discord.Message):
        if message.channel == self.DISCORD_INBOX_CHANNEL:
            data = json.loads(message.content)
            print(data)
            self.post_inbox(data['from'] + ': ' + data['subject'], emoji='📧', content=data['url'], url=data['url'])
            await message.add_reaction('\U0001f44d')
        else:
            print('bad')


async def setup(bot: commands.Bot) -> None:
    MY_GUILD = discord.Object(id=int(os.environ['DISCORD_GUILD_ID']))
    await bot.add_cog(Notion(bot), guild=MY_GUILD) 