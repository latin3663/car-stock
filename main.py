# -*- coding: utf-8 -*-
from flask import Flask, make_response
import os
from io import StringIO
import csv
import psycopg2
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TemplateSendMessage,
    CarouselTemplate,
    CarouselColumn,
    URIAction,
)

# 定数（環境変数から取得）
database_url = os.getenv('DATABASE_URL', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
app = Flask(__name__)
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def hello_world():
    return "hello world."


@app.route("/download/csv")
def download():

    f = StringIO()
    writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\n")

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:

            writer.writerow(["ID", "車種", "色", "ミッション", "走行距離", "年式", "車検", "価格", "URL", "データ取得日"])

            cur.execute("SELECT * FROM car_stock.stock")
            stockRows = cur.fetchall()

            for row in stockRows:
                writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]])

    res = make_response()
    res.data = f.getvalue()
    res.headers['Content-Type'] = 'text/csv'
    res.headers['Content-Disposition'] = 'attachment; filename=' + "car-stock" + '.csv'
    return res


def insertUserId(conn, cur, profile):
    cur.execute(
    "SELECT * FROM car_stock.line_user_id where user_id = '" + profile.user_id + "'")
    userIdRow = cur.fetchone()
    # 未登録のユーザーなら登録しておく
    if userIdRow is None:
        insertSql = "INSERT INTO car_stock.line_user_id VALUES ('" + profile.user_id + "')"
        # INSERT文 実行
        cur.execute(insertSql)
        # INSERT をコミット
        conn.commit()

    
@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:

            if event.type == "message":
                profile = line_bot_api.get_profile(event.source.user_id)
                messages = TextMessage(text="メッセージイベントを取得しました。\nYour ID:" + profile.user_id)
                
                insertUserId(conn, cur, profile)
                        
            elif event.type == "follow":
                messages = TextMessage(text="フォローイベントを取得しました。\nYour ID:" + profile.user_id)

                insertUserId(conn, cur, profile)

    status_msg = profile.status_message
    if status_msg != "None":
        status_msg = "なし"

    line_bot_api.reply_message(event.reply_token, messages=messages)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
