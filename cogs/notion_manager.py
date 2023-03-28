import os
import requests
import json
from pprint import pprint
from datetime import datetime, timezone

from discord import app_commands
from discord.ext import commands
import discord

from notion_client import Client
from notion_client.errors import APIResponseError

class NotionDB():
    def __init__(self) -> None:
        # Notion setup
        self.NOTION_API_KEY = os.environ['NOTION_API_KEY']
        self.NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
        self.NOTION_API_URL = "https://api.notion.com/v1/pages"

        self.notion = Client(auth=os.environ["NOTION_API_KEY"])

    def post(self, payload):
        # headers = {
        #     "Accept": "application/json",
        #     "Notion-Version": "2022-06-28",
        #     "Content-Type": "application/json",
        #     "Authorization": "Bearer " + self.NOTION_API_KEY,
        # }
        # try:
        #     response = requests.post(self.NOTION_API_URL, json=payload, headers=headers)
        # except Exception as e:
        #     print(f'Exception: {e}')
        # return response
    
        created_page = self.notion.pages.create(parent={"database_id": self.NOTION_DATABASE_ID}, properties=payload["properties"])
        return 

    # payload の末尾にコンテンツを追加する
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
                            "text": {"content": f"{title}"},
                        }
                    ]
                }
            },
            "children": []
        }
        return payload

    def query(self, filter):
        results = self.notion.databases.query(
            database_id=self.NOTION_DATABASE_ID,
            filter=filter
        )
        return results

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
        self.notion = Client(auth=os.environ["NOTION_API_KEY"])

        # Discord setup
        self.DISCORD_INBOX_CHANNEL = self.bot.get_channel(int(os.environ['DISCORD_INBOX_CHANNEL_ID']))

    # プロジェクトプロパティを編集
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

    def post_inbox(self, title: str, content='', url='', emoji='😐') -> str:
        payload = self.notion_db.default(title, emoji=emoji)
        payload = self.set_project(payload, os.environ['NOTION_INBOX_PROJECTS_TAG_IT'])
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
        created_page = self.notion.pages.create(parent={"database_id": self.NOTION_DATABASE_ID}, properties=payload["properties"])
        print(created_page)
        return created_page


    @app_commands.command()
    async def inbox(self, interaction: discord.Interaction, title: str) -> None:
        channel = interaction.channel
        interaction_id = interaction.id
        url = f"https://discord.com/channels/{channel.guild.id}/{channel.id}/{interaction_id}"
        message = self.post_inbox(title, url=url)
        await interaction.response.send_message("hogehoge!")

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

    @app_commands.command()
    async def daily_report(self, interaction: discord.Interaction) -> None:
        # 現在日時を取得
        now = datetime.now(timezone.utc)

        # 今日の日付を文字列に変換して取得
        today = now.strftime('%Y-%m-%d')

        # データベースのIDを取得する
        database_id = os.environ["NOTION_DATABASE_ID"]

        filter = {
            "and": [
                {
                    "property": "Document type",
                    "select": {
                        "equals": "Daily report"
                    }
                },
                {
                    "property": "Created",
                    "created_time": {
                        "on_or_after": today
                    }
                }
            ]
        }
        result = self.notion_db.query(filter=filter)
        pprint(result)



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
