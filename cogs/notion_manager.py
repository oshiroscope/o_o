from discord import app_commands
from discord.ext import commands
import discord
import os
import requests
import json

class NotionDB():
    def __init__(self) -> None:
        # Notion setup
        self.NOTION_API_KEY = os.environ['NOTION_API_KEY']
        self.NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
        self.NOTION_API_URL = "https://api.notion.com/v1/pages"

    def post(self, payload) -> requests.Response:
        headers = {
            "Accept": "application/json",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.NOTION_API_KEY,
        }
        try:
            response = requests.post(self.NOTION_API_URL, json=payload, headers=headers)
        except Exception as e:
            print(f'Exception: {e}')
        return response

    def add_child(self, payload: dict, child: dict) -> dict:
        if 'children' not in payload:
            payload['children'] = []
        payload['children'].append(child)
        return payload

    def default(self, title: str, emoji='') -> dict:
        payload = {
            "parent": {"database_id": self.NOTION_DATABASE_ID},
            "icon": {"emoji": emoji},
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {"content": title},
                        }
                    ]
                }
            },
            "children": []
        }
        return payload

    def set_project(self, payload: dict, id: str) -> dict:
        payload['properties']['Project'] = {
            'relation': [
                {
                    'id': id
                }
            ],
            'has_more': False
        }
        return payload

class NotionManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.notion_db = NotionDB()
        # Notion setup
        self.NOTION_API_KEY = os.environ['NOTION_API_KEY']
        self.NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
        self.NOTION_API_URL = "https://api.notion.com/v1/pages"

        # Discord setup
        self.DISCORD_INBOX_CHANNEL = self.bot.get_channel(int(os.environ['DISCORD_INBOX_CHANNEL_ID']))

    def post_inbox(self, title: str, content='', url='', emoji='😐') -> str:
        payload = self.notion_db.default(title, emoji=emoji)
        payload = self.notion_db.set_project(payload, os.environ['NOTION_INBOX_PROJECTS_TAG_IT'])
        payload = self.notion_db.add_child(payload,
        {
            "object": 'block',
            "type": "bookmark",
            "bookmark": 
            {
                "url": url
            }
        }
        )

        response = self.notion_db.post(payload)
        # response = requests.post(self.NOTION_API_URL, json=payload, headers=headers)
        result_dict = response.json()
        result = result_dict["object"]

        message = ""
        if result == "page":
            page_url = result_dict["url"]
            page_title = result_dict["properties"]["Name"]["title"][0]["text"]["content"]
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

    @app_commands.command()
    async def get_db(self, interaction: discord.Interaction) -> None:
        # url = f"https://api.notion.com/v1/databases/{self.NOTION_DATABASE_ID}"
        url = f"https://api.notion.com/v1/pages/c43646892163466ebfba427cd7225c1d"
        headers = {
            'Authorization': 'Bearer ' + self.NOTION_API_KEY,
            "Notion-Version": "2022-06-28",
        }
        r = requests.get(url, headers=headers)
        data = r.json()
        print(data)

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
    await bot.add_cog(NotionManager(bot), guild=MY_GUILD) 