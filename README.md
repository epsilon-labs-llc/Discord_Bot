# Discord Bot Collection

現在のところ、「AFKマネージャー ボット」と「コレクターボット」しかありませんが、今後もっとボットが作るかもしれないです。

## [AFKマネージャー ボット](https://github.com/epsilon-labs-llc/Discord_Bot/tree/main/afk_manager/README.md)

「AFKマネージャー」は、Discordサーバー内でAFK（離席）ユーザーを管理するためのボットです。このボットは、ボイスチャンネルで一定時間アクションがないユーザーを「ミュート部屋」に自動で移動し、サーバーミュートにします。さらに、ユーザーがミュート部屋から退出した際に、サーバーミュートを解除する機能もあります。

## [コレクターボット](https://github.com/epsilon-labs-llc/Discord_Bot/tree/main/collector_bot/README.md)

「コレクターボット」は、Discordサーバー内でメンバーがキャラクターを収集し、トレードやコレクションを楽しむためのボットです。ユーザーは毎日のログインボーナスやミッションをクリアしてアイテムを集め、最終的にコレクションを完成させることを目指します。特典やランキングも用意されており、ゲーム感覚で楽しめます。

## インストール方法

1. 必要なライブラリをインストール
    ```
    pip install -r requirements.txt
    ```
2. .env のテンプレートを参考に設定ファイルを設定

## 使用方法
ボットを起動するには、以下のコマンドを実行してください
```
python bot_name.py
```

## ライセンス

これらのすべてのボットは [MIT license](LICENSE) の下でライセンスされています。
