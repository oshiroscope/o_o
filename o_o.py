import discord
from discord.ext import commands
import os
import traceback

cogslist = [
    'cogs.notion'
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
        # tree = await self.tree.sync()
        # print(tree)

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(f'豊かな人生'))
        await self.tree.sync()
        await self.tree.sync(guild=self.MY_GUILD)

bot = o_o()
bot.run(os.environ['DISCORD_BOT_TOKEN'])        


# @bot.slash_command(guild_ids=[DISCORD_GUILD_ID])
# async def hello(
#     ctx,
#     name: Option(str, "名前を入力してください"),
#     gender: Option(str, "性別を選択してください", choices=["男性", "女性", "その他"]),
#     age: Option(int, "年齢を入力してください", required=False, default=18),
# ):
#     await ctx.respond(f"こんにちは、{name}さん")


# @bot.slash_command(guild_ids=[DISCORD_GUILD_ID])
# async def notion(
#     ctx,
#     title: Option(str, "名前を入力してください"),
# ):

#     url = "https://api.notion.com/v1/pages"

#     print("notion_api_key" + NOTION_API_KEY)
#     api_key = NOTION_API_KEY
#     database_id = NOTION_DATABASE_ID
#     emoji = "🤠"
#     headers = {
#         "Accept": "application/json",
#         "Notion-Version": "2022-06-28",
#         "Content-Type": "application/json",
#         "Authorization": "Bearer " + api_key,
#     }

#     payload = {
#         "parent": {"database_id": database_id},
#         "icon": {"emoji": emoji},
#         "properties": {
#             "Name": {
#                 "title": [
#                     {
#                         "text": {"content": name},
#                     }
#                 ],
#             },
#         },
#     }

#     response = requests.post(url, json=payload, headers=headers)
#     result_dict = response.json()
#     result = result_dict["object"]
#     page_url = result_dict["url"]
#     page_title = result_dict["properties"]["Name"]["title"][0]["text"]["content"]
#     print(page_title)

#     message = ""
#     if result == "page":
#         message = "「" + page_title + "」が作成されたよ～！！\n " + page_url
#     elif result == "error":
#         message = "なんかエラーが発生しているみたい！\n " + page_url
#     else:
#         message = ("例外起きて草。なんも分からん。\n " + page_url,)

#     await ctx.respond(message)

# bot.run(DISCORD_BOT_TOKEN)