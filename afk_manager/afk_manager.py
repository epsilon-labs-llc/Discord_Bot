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

# .envファイルの内容を読み込み
load_dotenv()

# 環境変数から取得
AFK_CHANNEL_ID = int(os.getenv("AFK_CHANNEL_ID"))
INACTIVITY_TIME = int(os.getenv("INACTIVITY_TIME", 900))  # デフォルト15分
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ユーザーのアクティビティ記録を保持する辞書
user_activity = {}

# 起動時イベント
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
        logging.warning("AFK channel not found")
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
                logging.info(f"{member.display_name} has been moved to the AFK channel and muted.")

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # ユーザーがミュート部屋から退出したかどうかを確認
    afk_channel = discord.utils.get(member.guild.voice_channels, id=AFK_CHANNEL_ID)

    # ユーザーがミュート部屋を離れた場合
    if before.channel == afk_channel and after.channel != afk_channel:
        if member.voice is not None:  # ユーザーがボイスチャンネルに接続しているか確認
            # サーバーミュートを解除
            await member.edit(mute=False)
            logging.info(f"{member.name} has left the AFK channel, and the mute has been lifted.")
    elif after.channel:
        user_activity[member.id] = asyncio.get_event_loop().time()
        logging.info(f"{member.name} has joined the voice channel: {after.channel.name}")
   

# スラッシュコマンド: /ミュート
@tree.command(name="ミュート", description="指定したユーザーをミュート部屋に移動します")
async def mute_user(interaction: discord.Interaction, user: discord.Member):
    # ユーザーがボイスチャンネルに接続しているか確認
    if user.voice is None:
        await interaction.response.send_message("指定されたユーザーはボイスチャンネルに接続していません。", ephemeral=True)
        logging.info(f"{interaction.user.name} attempted to mute, but the specified user is not connected.")
        return

    # ボイスチャンネルに接続している場合、"ミュート部屋"に移動
    afk_channel = discord.utils.get(interaction.guild.voice_channels, id=AFK_CHANNEL_ID)

    if afk_channel is None:
        await interaction.response.send_message("ミュート部屋が見つかりません。", ephemeral=True)
        logging.warning(f"{interaction.user.name} attempted to mute, but the AFK channel was not found.")
        return

    # "ミュート部屋"に移動
    await user.move_to(afk_channel)
    await user.edit(mute=True)
    # 応答がまだ送られていない場合のみ送るようにする
    if not interaction.response.is_done():
        await interaction.response.send_message(f"{user.name}さんをミュート部屋に移動し、ミュートしました。", ephemeral=True)
        logging.info(f"{interaction.user.name} has moved {user.name} to the AFK channel.")

# ボットを実行
client.run(BOT_TOKEN)