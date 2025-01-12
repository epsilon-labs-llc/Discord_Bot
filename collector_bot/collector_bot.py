import discord
from discord.ext import tasks
from discord import app_commands
import random
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime, timezone, timedelta
import pytz

# ログ設定
logging.basicConfig(
    filename="collector_bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# タイムゾーン設定
JST = pytz.timezone("Asia/Tokyo")

# .envファイルの内容を読み込み
load_dotenv()

# 環境変数から取得
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
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
    data = {"collections": {}, "login_streaks": {}, "last_used": {}}

# キャラクターリスト（名前と画像パス）
characters = {
    "normal": [
        {"name": "スライム", "image": "imgs/slime.gif"},
        {"name": "ゴブリン", "image": "imgs/goblin.gif"},
        {"name": "ダイコーン", "image": "imgs/daikon.gif"},
        {"name": "オーク", "image": "imgs/orc.gif"},
        {"name": "デビルカバ", "image": "imgs/devil-hippo.gif"},
        {"name": "ゴーレム", "image": "imgs/golem.gif"},
        {"name": "ファイヤー鶏", "image": "imgs/fire-chicken.gif"},
        {"name": "銀狼", "image": "imgs/silver-wolf.gif"},
        {"name": "ゾンビ", "image": "imgs/zombie.gif"},
        {"name": "鳥", "image": "imgs/bird.gif"},
    ],
    "rare": [
        {"name": "ワイバーン", "image": "imgs/wyvern.gif"},
        {"name": "ケロべロス", "image": "imgs/cerberus.gif"},
        {"name": "ワーウルフ", "image": "imgs/werewolf.gif"},
        {"name": "ミノタウロス", "image": "imgs/minotaur.gif"},
        {"name": "炎馬", "image": "imgs/flame-horse.gif"},
        {"name": "氷馬", "image": "imgs/ice-horse.gif"},
        {"name": "天狗", "image": "imgs/tengu.gif"},
    ],
    "super_rare": [
        {"name": "ドラゴン", "image": "imgs/dragon.gif"},
        {"name": "グリフォン", "image": "imgs/griffon.gif"},
        {"name": "白虎", "image": "imgs/white-tiger.gif"},
        {"name": "八岐大蛇", "image": "imgs/yamata-no-orochi.gif"},
        {"name": "朱雀", "image": "imgs/vermilion-bird.gif"},
    ],
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

# 起動時イベント
@client.event
async def on_ready():
    logging.info(f"Bot is online! Logged in as {client.user}")
    await tree.sync()
    logging.info("Slash commands synced.")

rarity_dict = {
    "normal": "ノーマル",
    "rare": "レア",
    "super_rare": "スーパーレア"
}

# コマンド: /デイリー
@tree.command(name="デイリー", description="毎日1枚のキャラクターをランダムで獲得します")
async def collect(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    now = datetime.now(JST)  # 現在時刻を東京時間で取得

    # 前回使用時刻の確認
    last_used_str = data.setdefault("last_used", {}).get(user_id)  # "last_used"がなければ初期化
    if last_used_str:
        last_used = datetime.fromisoformat(last_used_str)
        time_diff = now - last_used
        if time_diff < timedelta(hours=24):
            # 再使用までの残り時間を計算
            remaining_time = timedelta(hours=24) - time_diff
            remaining_hours = remaining_time.seconds // 3600  # 残り時間を時間単位で計算
            logging.info(f"User {user_id} attempted to use the daily command but needs to wait {remaining_hours} more hours.")
            await interaction.response.send_message(
                f"デイリーコマンドはまだ使用できません。あと **{remaining_hours}時間後** に使用できます。"
            )
            return

    # 新しい使用時刻を記録
    data["last_used"][user_id] = now.isoformat()
    logging.info(f"User {user_id} used the daily command at {now.isoformat()}.")

    # ログインボーナス処理
    streak = data.setdefault("login_streaks", {}).get(user_id, 0) + 1  # "login_streaks"がなければ初期化
    data["login_streaks"][user_id] = streak
    logging.info(f"User {user_id} login streak updated to {streak} days.")

    # キャラクター収集
    rarity, character = get_random_character()
    data.setdefault("collections", {}).setdefault(user_id, []).append(character["name"])  # "collections"がなければ初期化
    logging.info(f"User {user_id} collected a character: {character['name']} (Rarity: {rarity}).")

    save_data()

    # Embedでアイテム情報を表示
    embed = discord.Embed(
        title=f"今日のキャラクター: {character['name']}",
        description=f"レアリティ: **{rarity_dict[rarity]}**\nログイン連続日数: {streak}日",
        color=0xFFD700 if rarity == "super_rare" else 0x1E90FF if rarity == "rare" else 0x90EE90
    )
    file_path = character["image"]
    if os.path.exists(file_path):
        file = discord.File(file_path, filename="image.png")
        embed.set_thumbnail(url="attachment://image.png")
        await interaction.response.send_message(file=file, embed=embed)
    else:
        await interaction.response.send_message(f"画像が見つかりませんでした。")

    logging.info(f"User {user_id} collected {character['name']} ({rarity}) on day {streak}")

# Botの起動
client.run(BOT_TOKEN)