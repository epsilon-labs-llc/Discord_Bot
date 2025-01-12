import discord
from discord.ext import tasks
from discord import app_commands
from discord.ui import Button, View
from discord.errors import InteractionResponded
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

# コレクション保存の変更
def add_to_collection(user_id, rarity, character_name):
    # ユーザーのコレクションを取得
    user_collection = data["collections"].setdefault(user_id, {"normal": [], "rare": [], "super_rare": []})
    
    # 既存のキャラクターをチェックして、数量を増加させる
    for character in user_collection[rarity]:
        if character["name"] == character_name:
            character["quantity"] += 1
            return
    
    # 新しいキャラクターを追加
    user_collection[rarity].append({"name": character_name, "quantity": 1})

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

# コマンド: /ヘルプ
@tree.command(name="ヘルプ", description="すべてのコマンドとその説明を表示します")
async def help_command(interaction: discord.Interaction):
    commands_info = """
        **利用可能なコマンド一覧**
        `/デイリー` - 毎日1枚のキャラクターをランダムで獲得します。
        `/コレクション 表示` - あなたのコレクションを表示します。同じキャラクターの所持数も確認できます。
        `/コレクション リーダーボード` - 全メンバーのコレクション所持数をランキング形式で表示します。
        `ヘルプ` - すべてのコマンドとその説明を表示します。
    """
    await interaction.response.send_message(commands_info)
    logging.info("Help command executed.")

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
                f"デイリーコマンドはまだ使用できません。あと **{remaining_hours}時間後** に使用できます。", ephemeral=True
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
    add_to_collection(user_id, rarity, character["name"])  # コレクションにキャラクターを追加
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
        await interaction.response.send_message(file=file, embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(f"画像が見つかりませんでした。", ephemeral=True)

    logging.info(f"User {user_id} collected {character['name']} ({rarity}) on day {streak}")

# コマンド: /コレクション
@tree.command(name="コレクション", description="コレクション関連のコマンドです")
@app_commands.describe(action="表示またはリーダーボードを選択")
@app_commands.choices(
    action=[
        app_commands.Choice(name="表示", value="表示"),
        app_commands.Choice(name="リーダーボード", value="リーダーボード")
    ]
)
async def collection(interaction: discord.Interaction, action: str):
    user_id = str(interaction.user.id)

    if action == "表示":
        user_collection = data["collections"].get(user_id, {"normal": [], "rare": [], "super_rare": []})

        # レアリティ順に表示
        collection_text = ""
        for rarity in ["super_rare", "rare", "normal"]:
            if user_collection[rarity]:
                collection_text += f"\n**{rarity_dict[rarity]}**\n"
                for character in user_collection[rarity]:
                    collection_text += f"{character['name']}: {character['quantity']}体\n"

        if not collection_text:
            await interaction.response.send_message("あなたのコレクションは空です。デイリーコマンドでキャラクターを集めましょう！", ephemeral=True)
        else:
            await interaction.response.send_message(f"**あなたのコレクション:**\n{collection_text}", ephemeral=True)

        logging.info(f"User {user_id} checked their collection.")
    
    elif action == "リーダーボード":
        leaderboard = []

        for user_id, user_collection in data["collections"].items():
            # スーパーレア、レア、ノーマルの順にソート
            super_rare_count = sum(c["quantity"] for c in user_collection["super_rare"])
            rare_count = sum(c["quantity"] for c in user_collection["rare"])
            normal_count = sum(c["quantity"] for c in user_collection["normal"])
            total = (super_rare_count, rare_count, normal_count)
            leaderboard.append((user_id, total))

        # ソート (スーパーレア → レア → ノーマルの順)
        leaderboard.sort(key=lambda x: (x[1][0], x[1][1], x[1][2]), reverse=True)

        # 表示用テキスト生成
        leaderboard_text = "\n".join(
            [f"{index+1}位: <@{user_id}> - スーパーレア: {total[0]}体, レア: {total[1]}体, ノーマル: {total[2]}体"
             for index, (user_id, total) in enumerate(leaderboard)]
        )
        await interaction.response.send_message(f"**コレクション リーダーボード:**\n{leaderboard_text}")

        logging.info("Leaderboard command executed.")

# コマンド: /トレード
@tree.command(name="トレード", description="他のユーザーとアイテムを交換します")
async def trade(interaction: discord.Interaction, target: discord.User, あげるアイテム: str, もらうアイテム: str):
    user_id = str(interaction.user.id)
    target_id = str(target.id)

    # ユーザーとターゲットのコレクションを取得
    user_collection = data["collections"].get(user_id, {})
    target_collection = data["collections"].get(target_id, {})

    # ユーザーとターゲットのコレクションが存在するかを確認
    if not user_collection:
        await interaction.response.send_message("あなたのコレクションは空です。", ephemeral=True)
        return

    if not target_collection:
        await interaction.response.send_message("ターゲットのコレクションは空です。", ephemeral=True)
        return

    # あげるアイテムともらうアイテムがコレクションに存在するか確認
    user_has_item = False
    target_has_item = False

    # ユーザーのコレクション内であげるアイテムを探す
    for category in ["normal", "rare", "super_rare"]:
        for item in user_collection.get(category, []):
            if item["name"] == あげるアイテム:
                user_has_item = True
                break

    # ターゲットのコレクション内でもらうアイテムを探す
    for category in ["normal", "rare", "super_rare"]:
        for item in target_collection.get(category, []):
            if item["name"] == もらうアイテム:
                target_has_item = True
                break

    # アイテムがコレクションに存在しない場合
    if not user_has_item:
        await interaction.response.send_message(f"指定されたアイテム `{あげるアイテム}` は、あなたのコレクションに存在しません。", ephemeral=True)
        return

    if not target_has_item:
        await interaction.response.send_message(f"指定されたアイテム `{もらうアイテム}` は、ターゲットのコレクションに存在しません。", ephemeral=True)
        return
    
    # トレード確認メッセージ
    confirm_message = f"あなたは {target.mention} とアイテム `{あげるアイテム}` と `{もらうアイテム}` を交換しようとしています。トレードを承諾しますか？"

    # ボタンを作成
    accept_button = Button(label="承諾", style=discord.ButtonStyle.green)
    reject_button = Button(label="却下", style=discord.ButtonStyle.red)

    # 状態を追跡する変数
    trade_accepted_by_user = False
    trade_accepted_by_target = False

    # 承諾ボタンのコールバック
    async def accept_callback(interaction: discord.Interaction):
        nonlocal trade_accepted_by_user, trade_accepted_by_target
        if interaction.user == interaction.guild.owner:  # ユーザーが承諾した場合
            trade_accepted_by_user = True
        elif interaction.user == target:  # ターゲットが承諾した場合
            trade_accepted_by_target = True

        try:
            if trade_accepted_by_user and trade_accepted_by_target:
                # ユーザーのコレクションを検索し、指定されたアイテムを見つける
                item_found = False
                for category in ["normal", "rare", "super_rare"]:
                    for item in user_collection.get(category, []):
                        if item["name"] == あげるアイテム:
                            item_found = True
                            # アイテムの数量を減らす
                            item["quantity"] -= 1
                            # アイテムの数量が0になった場合、アイテムをコレクションから削除する
                            if item["quantity"] == 0:
                                user_collection[category].remove(item)
                            break

                # アイテムが見つからない場合、エラーメッセージを表示
                if not item_found:
                    await interaction.response.send_message(f"指定されたアイテム `{あげるアイテム}` は、あなたのコレクションに存在しません。", ephemeral=True)
                    return

                # ターゲットのコレクションを更新（アイテムを追加）
                item_found = False
                for category in ["normal", "rare", "super_rare"]:
                    for item in target_collection.get(category, []):
                        if item["name"] == もらうアイテム:
                            item_found = True
                            # アイテムの数量を減らす
                            item["quantity"] -= 1
                            if item["quantity"] == 0:
                                target_collection[category].remove(item)
                            break
                if not item_found:
                    await interaction.response.send_message(f"ターゲットのアイテム `{もらうアイテム}` が見つかりませんでした。", ephemeral=True)
                    return

                # アイテム交換処理完了メッセージ
                save_data()

                # ボタン無効化
                accept_button.disabled = True
                reject_button.disabled = True
                await interaction.edit_message(view=view)

                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"{interaction.user.mention} と {target.mention} がアイテムを交換しました！\n"
                        f"{interaction.user.mention} は **{もらうアイテム}** を獲得し、**{あげるアイテム}** を失いました。\n"
                        f"{target.mention} は **{あげるアイテム}** を獲得し、**{もらうアイテム}** を失いました。"
                    )

                logging.info(f"Trade completed between {interaction.user.id} and {target.id}: {あげるアイテム} <-> {もらうアイテム}")
            else:
                await interaction.response.send_message(f"{interaction.user.mention} はトレードを承諾しました。", ephemeral=True)

        except InteractionResponded:
            # すでに応答が完了している場合の処理
            logging.info("Interaction already responded, no further response will be sent.")

    # 却下ボタンのコールバック
    async def reject_callback(interaction: discord.Interaction):
        nonlocal trade_accepted_by_user, trade_accepted_by_target
        if interaction.user == interaction.guild.owner:
            trade_accepted_by_user = False
        elif interaction.user == target:
            trade_accepted_by_target = False

        await interaction.response.send_message(f"{interaction.user.mention} はトレードを却下しました。", ephemeral=True)

        # ボタンを無効化
        accept_button.disabled = True
        reject_button.disabled = True
        await interaction.edit_message(view=view)

    # ボタンのコールバックを設定
    accept_button.callback = accept_callback
    reject_button.callback = reject_callback

    # ビューを作成してボタンを追加
    view = View()
    view.add_item(accept_button)
    view.add_item(reject_button)

    # トレード確認メッセージを送信
    await interaction.response.send_message(confirm_message, view=view)

# Botの起動
client.run(BOT_TOKEN)