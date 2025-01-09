import discord
from discord.ext import tasks
from discord import app_commands
import asyncio
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timezone, timedelta

# ログ設定
logging.basicConfig(
    filename="afk_manager_bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# タイムゾーン設定 (Asia/Tokyo)
JST = timezone(timedelta(hours=9))

# .envファイルの内容を読み込み
load_dotenv()

# 環境変数から取得
AFK_CHANNEL_ID = int(os.getenv("AFK_CHANNEL_ID"))
INACTIVITY_TIME = int(os.getenv("INACTIVITY_TIME", 900))  # デフォルト15分
AFK_BOT_TOKEN = os.getenv("AFK_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ユーザーのアクティビティ記録を保持する辞書
user_activity = {}

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("AFKユーザーを監視中..."))
    logging.info(f"Bot is online! Logged in as {client.user}")
    check_inactivity.start()
    await tree.sync()
    logging.info("Slash commands synced.")

@tasks.loop(seconds=60)  # 1分ごとにチェック
async def check_inactivity():
    current_time = asyncio.get_event_loop().time()
    guild = discord.utils.get(client.guilds)
    if not guild:
        return

    afk_channel = guild.get_channel(AFK_CHANNEL_ID)
    if not afk_channel:
        logging.warning("ミュート部屋が見つかりません")
        return

    for voice_channel in guild.voice_channels:
        if voice_channel.id == AFK_CHANNEL_ID:
            continue

        for member in voice_channel.members:
            last_active = user_activity.get(member.id, None)
            if last_active and current_time - last_active > INACTIVITY_TIME:
                await member.move_to(afk_channel)
                await member.edit(mute=True)  # サーバーミュートを適用
                user_activity.pop(member.id, None)
                logging.info(f"{member.display_name} さんをミュート部屋に移動し、サーバーミュートしました。")

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # ユーザーがミュート部屋から退出したかどうかを確認
    afk_channel = discord.utils.get(member.guild.voice_channels, id=AFK_CHANNEL_ID)

    # ユーザーがミュート部屋を離れた場合
    if before.channel == afk_channel and after.channel != afk_channel:
        # サーバーミュートを解除
        await member.edit(mute=False)
        print(f"{member.name}さんのサーバーミュートを解除しました。")

# スラッシュコマンド: /ミュート
@tree.command(name="ミュート", description="指定したユーザーをミュート部屋に移動します")
async def mute_user(interaction: discord.Interaction, user: discord.Member):
    # ユーザーがボイスチャンネルに接続しているか確認
    if user.voice is None:
        await interaction.response.send_message("指定されたユーザーはボイスチャンネルに接続していません。", ephemeral=True)
        return

    # ボイスチャンネルに接続している場合、"ミュート部屋"に移動
    afk_channel = discord.utils.get(interaction.guild.voice_channels, id=AFK_CHANNEL_ID)

    if afk_channel is None:
        await interaction.response.send_message("ミュート部屋が見つかりません。", ephemeral=True)
        return

    # "ミュート部屋"に移動
    await user.move_to(afk_channel)
    await user.edit(mute=True)
    # 応答がまだ送られていない場合のみ送るようにする
    if not interaction.response.is_done():
        await interaction.response.send_message(f"{user.name}さんをミュート部屋に移動し、ミュートしました。", ephemeral=True)

# ボットを実行
client.run(AFK_BOT_TOKEN)
