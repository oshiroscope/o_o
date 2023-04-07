import os
import requests
import json
from pprint import pprint
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from discord import app_commands
from discord.ext import commands
import discord

from notion_client import Client
from notion_client.errors import APIResponseError

from typing import Literal

projects = []
notion = Client(auth=os.environ["NOTION_API_KEY"])

projects_database_id = os.environ["NOTION_PROJECTS_DATABASE_ID"]

filter_projects = {
    "property": "Status",
    "status": {
        "equals": "Ongoing"
    }
}

result = notion.databases.query(
    database_id=projects_database_id,
    filter=filter_projects
)

if 'results' in result:
    for r in result['results']:
        title = r['properties']["Name"]['title'][0]['text']['content']
        id = r['id']
        projects.append(discord.app_commands.Choice(name=title, value=id))

class NotionManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        # self.d = NotionDB()

        # Notion setup
        self.NOTION_API_KEY = os.environ['NOTION_API_KEY']
        self.NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
        self.NOTION_API_URL = "https://api.notion.com/v1/pages"
        # self.notion = Client(auth=os.environ["NOTION_API_KEY"])
        self.notion = notion 

        # Discord setup
        self.DISCORD_INBOX_CHANNEL = self.bot.get_channel(int(os.environ['DISCORD_INBOX_CHANNEL_ID']))

    def post_inbox(self, title: str, content='', url='', emoji='😐', project_id='') -> str:
        _project_id = project_id
        if _project_id == None:
            _project_id = os.environ['NOTION_INBOX_PROJECTS_TAG_IT']
        
        properties = {
            # page title
            "Name": {
                "title": [
                    {
                        "text": {"content": f"{title}"},
                    }
                ]
            },
            # Project は Tag it!
            "Project": {
                "relation": [
                    {
                        "id": _project_id
                    }
                ],
                "has_more": False
            }
        }
        child = {
            "object": 'block',
            "type": "bookmark",
            "bookmark": 
            {
                "url": url
            }
        }
        created_page = self.notion.pages.create(parent={"database_id": self.NOTION_DATABASE_ID}, properties=properties, children=[child])
        return created_page

    @app_commands.command()
    @app_commands.choices(project_id = projects)
    async def inbox(self, interaction: discord.Interaction, title: str, project_id: str = None) -> None:
        channel = interaction.channel
        interaction_id = interaction.id
        url = f"https://discord.com/channels/{channel.guild.id}/{channel.id}/{interaction_id}"
        new_page = self.post_inbox(title, url=url, project_id=project_id)
        await interaction.response.send_message(f"{title} をつくったよ！ {new_page['url']}")

    @app_commands.command()
    async def daily_report(self, interaction: discord.Interaction) -> None:
        channel = interaction.channel

        # JST タイムゾーンを設定
        JST = timezone(timedelta(hours=9))

        # JST タイムゾーンで今日の日付を取得
        today = datetime.now(JST).date()

        # 今日のタイムスタンプをISOフォーマットに変換
        today_iso = today.isoformat()

        # データベースのIDを取得する
        database_id = os.environ["NOTION_DATABASE_ID"]

        filter_daily_report = {
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
                        "on_or_after": today_iso + "T00:00:00+09:00"
                    }
                }
            ]
        }

        result = self.notion.databases.query(
            database_id=self.NOTION_DATABASE_ID,
            filter=filter_daily_report
        )
        if 'results' in result:
            for r in result['results']:
                author = r['properties']['Created by']['created_by']['name']
                author_id = r['properties']['Created by']['created_by']['id']
                page_id = r['id']

                # ページの情報を取得する関数
                def get_page_info(page):
                    # # ページの情報を取得
                    # page = self.notion.pages.retrieve(page_id)
                    # # ページのタイトル
                    title = page['properties']["Name"]['title'][0]['text']['content']
                    # ページの子ブロック
                    children = self.notion.blocks.children.list(page['id']).get("results")
                    # children = page['children'].list()
                    return title, children
                
                # # Discord Embedに変換する関数
                # def block_to_embed(block):
                #     # ブロックがテキストの場合
                #     if block['type'] == "paragraph":
                #         text = block['paragraph']['rich_text'][0]['plain_text']
                #         return discord.Embed(description=text)
                #     # ブロックが画像の場合
                #     elif block['type'] == "embed":
                #         return discord.Embed().set_image(url=block['embed']['url'])
    
                def block_to_text(block, prefix=''):
                    type = block["type"]
                    text = ''

                    if type == 'embed':
                        text = f"{block['embed']['url']}\n"

                    elif 'rich_text' in block[type] and block[type]['rich_text'] != []:
                        text = block[type]['rich_text'][0]['plain_text']
                        if type == 'paragraph':
                            text = text
                        elif type == 'heading_1':
                            text = '***' + text + '***'
                        elif type == 'heading_2':
                            text = '**' + text + '**'
                        elif type == 'heading_3':
                            text = '__' + text + '__'
                        elif type in ['bulleted_list_item', 'numbered_list_item'] :
                            text = '- ' + text    
                        elif type == 'to_do':
                            status = block['to_do']['checked']
                            if status:
                                text = f"[x] {text}"
                            else:
                                text = f"[ ] {text}"
                        elif type == 'toggle':
                            text = '> ' + text
                        elif type == 'quote':
                            text = '> ' + text
                        elif type == 'code':
                            text = f"```{block['code']['language']}\n{block['code']['rich_text'][0]['text']['content']}```\n"
                        if block['has_children']:
                                children = self.notion.blocks.children.list(block_id=block['id'])
                                for child in children['results']:
                                    text += '\n' + block_to_text(child, prefix=prefix+'　') # Zenkaku space character

                    return prefix + text
                    

                # NotionページをDiscord Embedに変換する関数
                def page_to_embed(page):
                    # ページの情報を取得
                    title, children = get_page_info(page)
                    # Embedオブジェクトを作成
                    embed = discord.Embed(title=title)
                    
                    # 子ブロックを文字列に変換
                    children_text = ""
                    for block in children:
                        children_text = block_to_text(block)
                        if len(children_text) >= 1000:
                            children_text = children_text[:1000] + "..."
                        embed.add_field(name='', value=children_text, inline=False)
                    return embed
                
                # NotionページをDiscord Embedに変換
                embed = page_to_embed(r)
                embed.url = r['url']
                
                # Discordに投稿
                await channel.send(content=f"今日の {author} の日誌だよ！",embed=embed)
                
                today = datetime.now().date()
                filter_task = {
                    "and": [
                        {
                            "or": [
                                {
                                    "property": "GTD",
                                    "select": {
                                        "equals": "💪 Next actions"
                                    }
                                },
                                {
                                    "property": "GTD",
                                    "select": {
                                        "equals": "🔥 Do it!"
                                    }
                                }
                            ]
                        },
                        {
                            "property": "Person",
                            "people": {
                                "contains": author_id
                            }
                        },
                        {
                            "property": "Done?",
                            "checkbox": {
                                "equals": True
                            }
                        },
                        {
                            "property": "Last edited time",
                            "date": {
                                "on_or_after": today.isoformat()
                            }
                        },
                    ]
                }
                
                done = self.notion.databases.query(
                    database_id=self.NOTION_DATABASE_ID,
                    filter=filter_task
                )
                embed = discord.Embed(title="お疲れ～")
                text = ''
                for page in done["results"]:
                    # icon = page['icon']['emoji']
                    project_title = ''
                    if page['properties']['Project']['relation'] != []:
                        project = self.notion.pages.retrieve(page['properties']['Project']['relation'][0]['id'])
                        project_title = project['properties']['Name']['title'][0]['text']['content'] + ' :: '
                        
                    text += project_title + page['properties']['Name']['title'][0]['text']['content'] + '\n'

                embed.add_field(name='', value=text)
                await channel.send(content=f"今日 {author} が終わらせたタスクだよ！",embed=embed)



    @commands.Cog.listener(name='on_message')
    async def good_reaction(self, message: discord.Message):
        if message.channel == self.DISCORD_INBOX_CHANNEL:
            data = json.loads(message.content)
            print(data)
            self.post_inbox(data['from'] + ': ' + data['subject'], emoji='📧', content=data['url'], url=data['url'])
            await message.add_reaction('\U0001f44d')


async def setup(bot: commands.Bot) -> None:
    MY_GUILD = discord.Object(id=int(os.environ['DISCORD_GUILD_ID']))
    await bot.add_cog(NotionManager(bot), guild=MY_GUILD) 
