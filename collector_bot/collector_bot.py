import discord
from discord.ext import tasks
from discord import app_commands
import random
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime, timezone, timedelta

# ログ設定
logging.basicConfig(
    filename="collector_bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# タイムゾーン設定 (Asia/Tokyo)
JST = timezone(timedelta(hours=9))

# .envファイルの内容を読み込み
load_dotenv()

# 環境変数から取得
TOKEN = os.getenv("DISCORD_TOKEN")
RARITY_PROBABILITIES = {
    "normal": float(os.getenv("RARITY_NORMAL", 0.7)),
    "rare": float(os.getenv("RARITY_RARE", 0.2)),
    "super_rare": float(os.getenv("RARITY_SUPER_RARE", 0.1))
}

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# データ保存ファイル
DATA_FILE = "collections.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
else:
    data = {"collections": {}, "login_streaks": {}}

# キャラクターリスト（名前と画像パス）
characters = {
    "normal": [
        {"name": "スライム", "image": "imgs/slime.png"},
        {"name": "スケルトン", "image": "imgs/skeleton.png"},
        {"name": "ゴブリン", "image": "imgs/goblin.png"}
    ],
    "rare": [
        {"name": "フェニックス", "image": "imgs/phoenix.png"},
        {"name": "グリフォン", "image": "imgs/griffon.png"},
        {"name": "ユニコーン", "image": "imgs/unicorn.png"}
    ],
    "super_rare": [
        {"name": "ドラゴン", "image": "imgs/dragon.png"},
        {"name": "神獣ケルベロス", "image": "imgs/cerberus.png"},
        {"name": "古代巨人", "image": "imgs/giant.png"}
    ]
}

# データ保存
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# ランダムキャラクター取得
def get_random_character():
    rarity = random.choices(
        ["normal", "rare", "super_rare"],
        weights=[
            RARITY_PROBABILITIES["normal"],
            RARITY_PROBABILITIES["rare"],
            RARITY_PROBABILITIES["super_rare"]
        ],
        k=1
    )[0]
    character = random.choice(characters[rarity])
    return rarity, character

@client.event
async def on_ready():
    logging.info(f"Bot is online! Logged in as {client.user}")
    await tree.sync()
    logging.info("Slash commands synced.")

# コマンド: /collect daily
@tree.command(name="collect")
async def collect(ctx, mode: str):
    user_id = str(ctx.author.id)
    if mode == "daily":
        # ログインボーナス処理
        streak = data["login_streaks"].get(user_id, 0) + 1
        data["login_streaks"][user_id] = streak

        rarity, character = get_random_character()
        data["collections"].setdefault(user_id, []).append(character["name"])

        save_data()

        # Embedでアイテム情報を表示
        embed = discord.Embed(
            title=f"今日のキャラクター: {character['name']}",
            description=f"レアリティ: **{rarity.capitalize()}**\nログイン連続日数: {streak}日",
            color=0xFFD700 if rarity == "super_rare" else 0x1E90FF if rarity == "rare" else 0x90EE90
        )
        file_path = character["image"]
        if os.path.exists(file_path):
            file = discord.File(file_path, filename="image.png")
            embed.set_image(url="attachment://image.png")
            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(f"{character['name']} の画像が見つかりませんでした。")
        
        logging.info(f"User {user_id} collected {character['name']} ({rarity}) on day {streak}")
    else:
        await ctx.send("利用可能なモードは: `daily` です。")

# 起動時イベント
@client.event
async def on_ready():
    logging.info(f"Bot logged in as {client.user}")
    print(f"Bot logged in as {client.user}")

# Botの起動
client.run(TOKEN)