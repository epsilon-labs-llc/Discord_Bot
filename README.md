# Discord Bot Collection

現在のところ、「AFKマネージャー」ボットしかありませんが、今後新しいボットが作るかもしれないです。

## AFKマネージャー ボット

「AFKマネージャー」は、Discordサーバー内でAFK（離席）ユーザーを管理するためのボットです。このボットは、ボイスチャンネルで一定時間アクションがないユーザーを「ミュート部屋」に自動で移動し、サーバーミュートにします。さらに、ユーザーがミュート部屋から退出した際に、サーバーミュートを解除する機能もあります。

### 主な機能

- **AFKユーザーの自動移動**: 指定した時間内にアクションがないユーザーを「ミュート部屋」に移動します。
- **サーバーミュート**: ユーザーをミュート部屋に移動する際に、サーバーミュートを適用します。
- **サーバーミュート解除**: ユーザーがミュート部屋から退出すると、自動的にサーバーミュートが解除されます。
- **コマンド実行**: 特定のユーザーを手動で「ミュート部屋」に移動させ、ミュートを適用できます。

### 必要な権限

ボットが正常に動作するためには、以下の権限が必要です

#### 1. **全体の権限**
   - **View Channels (チャンネルの閲覧)**: ボットがチャンネルにアクセスできるようにするための基本的な権限です。

#### 2. **テキストチャンネルの権限の権限**
   - **Send Messages (メッセージを送信)**: ボットがテキストチャンネルでメッセージを送る場合に必要です。
   - **Read Message History (メッセージ履歴を読む)**: テキストチャンネル内のメッセージ履歴を確認する場合に必要です（監視のため）。
   - **Use Slash Commands (スラッシュコマンドを使用)**: スラッシュコマンドを利用するために必要です。

#### 3. **ボイスチャンネルの権限**
   - **Connect (接続)**: ボイスチャンネルに接続するために必要です。
   - **Mute Members (メンバーをミュート)**: ボイスチャンネルでメンバーをサーバーミュートする機能のために必要です。
   - **Move Members (メンバーを移動)**: 他のユーザーをAFKチャンネルなど別のボイスチャンネルに移動するために必要です。

### ログ

ボットの動作は `afk_manager_bot.log` にログとして記録されます。これにより、ボットのアクティビティを追跡することができます。

## ライセンス

このプロジェクトは [MIT License](LICENSE) の下でライセンスされています。
