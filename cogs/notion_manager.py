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
        self.notion = Client(auth=os.environ["NOTION_API_KEY"])

        # Discord setup
        self.DISCORD_INBOX_CHANNEL = self.bot.get_channel(int(os.environ['DISCORD_INBOX_CHANNEL_ID']))

    def post_inbox(self, title: str, content='', url='', emoji='😐') -> str:
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
                        "id": os.environ['NOTION_INBOX_PROJECTS_TAG_IT']
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
    async def inbox(self, interaction: discord.Interaction, title: str) -> None:
        channel = interaction.channel
        interaction_id = interaction.id
        url = f"https://discord.com/channels/{channel.guild.id}/{channel.id}/{interaction_id}"
        new_page = self.post_inbox(title, url=url)
        await interaction.response.send_message("hogehoge!")

    @app_commands.command()
    async def daily_report(self, interaction: discord.Interaction) -> None:
        channel = interaction.channel

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

        result = self.notion.databases.query(
            database_id=self.NOTION_DATABASE_ID,
            filter=filter
        )
        if 'results' in result:
            for r in result['results']:
                author = r['properties']['Created by']['created_by']['name']
                print(r['properties']['Created by']['created_by']['name'])
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
                
                # Discord Embedに変換する関数
                def block_to_embed(block):
                    # ブロックがテキストの場合
                    if block['type'] == "paragraph":
                        print(block['paragraph']['rich_text'])
                        text = block['paragraph']['rich_text'][0]['plain_text']
                        return discord.Embed(description=text)
                    # ブロックが画像の場合
                    elif block['type'] == "embed":
                        return discord.Embed().set_image(url=block['embed']['url'])
    
                # NotionページをDiscord Embedに変換する関数
                def page_to_embed(page):
                    # ページの情報を取得
                    title, children = get_page_info(page)
                    # Embedオブジェクトを作成
                    embed = discord.Embed(title=title)
                    
                    # ページの子ブロックをEmbedに追加
                    # for child in children:
                    #     embed.add_field(name='', value=block_to_embed(child), inline=False)
                    # 子ブロックを文字列に変換
                    children_text = ""
                    for block in children:
                        block_type = block["type"]
                        if block_type == "paragraph" and block["paragraph"]["rich_text"] != []: 
                            children_text = block["paragraph"]["rich_text"][0]["plain_text"] + "\n"
                        elif block_type == "heading_1" and block["heading_1"]["rich_text"] != []:
                            children_text = f"**{block['heading_1']['rich_text'][0]['plain_text']}**\n"
                        elif block_type == "heading_2" and block["heading_2"]["rich_text"] != []:
                            children_text = f"__{block['heading_2']['rich_text'][0]['plain_text']}__\n"
                        elif block_type == "heading_3" and block['heading_3']['rich_text'] != []:
                            children_text = f"{block['heading_3']['rich_text'][0]['plain_text']}\n"
                        elif block_type == "bulleted_list_item" and block['bulleted_list_item']['rich_text'] != []:
                            children_text = f"- {block['bulleted_list_item']['rich_text'][0]['plain_text']}\n"
                        elif block_type == "numbered_list_item" and block['numbered_list_item']['rich_text'] != []:
                            children_text = f"{block['numbered_list_item']['rich_text'][0]['plain_text']}\n"
                        elif block_type == "to_do" and block['to_do']['rich_text'] != []:
                            status = block['to_do']['checked']
                            text = block['to_do']['rich_text'][0]['plain_text']
                            if status:
                                children_text = f"[x] {text}\n"
                            else:
                                children_text = f"[ ] {text}\n"
                        elif block_type == "toggle" and block['toggle']['rich_text'] != []:
                            children_text = f"> {block['toggle']['rich_text'][0]['plain_text']}\n"
                        elif block_type == "quote" and block['quote']['rich_text'] != []:
                            children_text = f"> {block['quote']['rich_text'][0]['plain_text']}\n"
                        elif block_type == "code" and block['code']['rich_text'] != []:
                            print(block)
                            children_text = f"```{block['code']['language']}\n{block['code']['rich_text'][0]['text']['content']}```\n"
                        elif block_type == "embed":
                            children_text = f"{block['embed']['embed_url']}\n"
                        else:
                            children_text = "\n"

                        if len(children_text) >= 1000:
                            children_text = children_text[:1000] + "..."
                        embed.add_field(name='', value=children_text, inline=False)
                    # embed.add_field(name="Content", value=children_text, inline=False)
                    return embed
                
                # NotionページをDiscord Embedに変換
                embed = page_to_embed(r)
                # Discordに投稿
                await channel.send(content=f"今日の {author} の日誌だよ！",embed=embed)

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
