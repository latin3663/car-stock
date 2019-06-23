# coding: UTF-8
import requests
from bs4 import BeautifulSoup
import os
import psycopg2
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (
    TextMessage,
    TemplateSendMessage,
    CarouselTemplate,
    CarouselColumn,
    URIAction,
)

# 定数
# DATABASE_URL = "host=localhost port=5432 dbname=postgres user=postgres password=root"
database_url = os.getenv('DATABASE_URL', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
UA = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Mobile Safari/537.36'
headers = {'User-Agent': UA}


# 指定されたURLのBeautifulSoupを返す
def getSoup(url):
    res = requests.get(url, headers)
    res.encoding = res.apparent_encoding
    return BeautifulSoup(res.text, "html.parser")


line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
soup = getSoup("http://www.cornerstones.jp/stocklist")

# ページの最大値を取得(ページボタンの数をカウント)
maxPage = len(soup.select("#wpv-view-layout-1911-TCPID1869 > div.page.text-center.main-text > ul > li"))

insertCount = 0
newStocks = []

# ページの分だけループ
for pageIndex in range(1, maxPage+1):

    # {pageIndex}ページ目のストックリストへアクセス
    soup = getSoup("http://www.cornerstones.jp/stocklist?wpv_view_count=1911-TCPID1869&wpv_paged=" + str(pageIndex))

    # ページ内の在庫一覧を取得
    carDivs = soup.select("#wpv-view-layout-1911-TCPID1869 > div.col-xs-6")

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
        
            # 在庫の分だけループ
            for carDiv in carDivs:
                carLink = carDiv.select("div > a")[0]["href"]
                # ID
                id = str(carLink).split("/")
                id = "'" + id[len(id) - 1] + "'"
            
                cur.execute("SELECT * FROM car_stock.stock where id = " + id)
                stockRow = cur.fetchone()

                if stockRow is not None:
                    break
                
                soup = getSoup(carLink)
                specs = soup.select("div.top-spec")

                insertSql = "INSERT INTO car_stock.stock VALUES ("

                # 車種など
                newStock = {
                    "ID" : id,
                    "車種" : str(specs[0].text).strip(),
                    "カラー" : str(specs[1].text).strip(),
                    "ミッション" : str(specs[2].text).strip(),
                    "走行距離" : str(specs[3].text).strip(),
                    "年式" : str(specs[4].text).strip(),
                    "車検" : str(specs[5].text).strip(),
                    "価格" : str(specs[6].text).strip(),
                    "URL" : carLink,
                }
                
                insertSql += id
                insertSql += ", '" + str(specs[0].text).strip() + "'"
                insertSql += ", '" + str(specs[1].text).strip() + "'"
                insertSql += ", '" + str(specs[2].text).strip() + "'"
                insertSql += ", '" + str(specs[3].text).strip() + "'"
                insertSql += ", '" + str(specs[4].text).strip() + "'"
                insertSql += ", '" + str(specs[5].text).strip() + "'"
                insertSql += ", '" + str(specs[6].text).strip() + "'"
                insertSql += ", '" + carLink + "'"
                insertSql += ", current_date "
                insertSql += ")"
                print(insertSql)

                # INSERT文 実行
                cur.execute(insertSql)
                # INSERT をコミット
                conn.commit()

                # 通知メッセージ用にデータを保持しておく
                newStocks.append(newStock)
                insertCount += 1
                break


# if insertCount > 0:
if insertCount >= 0:
    stockColumns = []
    for newStock in newStocks:
        stockColumns.append(
            CarouselColumn(
                text=newStock["車種"] + "\n" + newStock["価格"],
                actions=[
                    URIAction(
                        type="uri",
                        label="開く",
                        uri=newStock["URL"],
                    ),
                ]
            )
        )
    
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
        
            cur.execute("SELECT user_id FROM car_stock.line_user_id")
            userIdRows = cur.fetchall()

            templateMessage = TemplateSendMessage(
                alt_text='在庫車両に追加がありました',
                template=CarouselTemplate(
                    type="carousel",
                    columns=stockColumns,
                )
            )

            # messages = TextMessage(text="新規の在庫がありました")
            for userIdRow in userIdRows:
                line_bot_api.push_message(userIdRow[0], templateMessage)

