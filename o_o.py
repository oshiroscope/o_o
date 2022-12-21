import discord
from discord.commands import Option
import requests
import json
import datetime


config_file = open("config.json", "r")
config = json.load(config_file)

bot = discord.Bot()


@bot.slash_command(guild_ids=[config["discord_guild_id"]])
async def ping(ctx):
    await ctx.respond("pong")


@bot.slash_command(guild_ids=[config["discord_guild_id"]])
async def hello(
    ctx,
    name: Option(str, "名前を入力してください"),
    gender: Option(str, "性別を選択してください", choices=["男性", "女性", "その他"]),
    age: Option(int, "年齢を入力してください", required=False, default=18),
):
    await ctx.respond(f"こんにちは、{name}さん")


@bot.slash_command(guild_ids=[config["discord_guild_id"]])
async def notion(
    ctx,
    name: Option(str, "名前を入力してください"),
):

    url = "https://api.notion.com/v1/pages"

    print("notion_api_key" + config["notion_api_key"])
    api_key = config["notion_api_key"]
    database_id = config["notion_database_id"]
    emoji = "🤠"
    headers = {
        "Accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }

    payload = {
        "parent": {"database_id": database_id},
        "icon": {"emoji": emoji},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {"content": name},
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
    print(page_title)

    message = ""
    if result == "page":
        message = "「" + page_title + "」が作成されたよ～！！\n " + page_url
    elif result == "error":
        message = "なんかエラーが発生しているみたい！\n " + page_url
    else:
        message = ("例外起きて草。なんも分からん。\n " + page_url,)

    await ctx.respond(message)


bot.run(config["discord_bot_token"])
