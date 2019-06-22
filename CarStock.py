# coding: UTF-8
import requests
from bs4 import BeautifulSoup
import os
import psycopg2

# 定数
# DATABASE_URL = "host=localhost port=5432 dbname=postgres user=postgres password=root"
DATABASE_URL = os.getenv('DATABASE_URL', None)
UA = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Mobile Safari/537.36'

def main():

    headers = {'User-Agent': UA}
    res = requests.get("http://www.cornerstones.jp/stocklist", headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    # ページの最大値を取得(ページボタンの数をカウント)
    maxPage = len(soup.select("#wpv-view-layout-1911-TCPID1869 > div.page.text-center.main-text > ul > li"))

    # ページの分だけループ
    for pageIndex in range(1, maxPage+1):

        # {pageIndex}ページ目のストックリストへアクセス
        url = "http://www.cornerstones.jp/stocklist?wpv_view_count=1911-TCPID1869&wpv_paged=" + str(pageIndex)
        res = requests.get(url, headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        # ページ内の在庫一覧を取得
        carDivs = soup.select("#wpv-view-layout-1911-TCPID1869 > div.col-xs-6")

        with psycopg2.connect(DATABASE_URL) as conn:
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
                    
                    res = requests.get(carLink, headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    specs = soup.select("div.top-spec")

                    insertSql = "INSERT INTO car_stock.stock VALUES ("

                    # 車種など
                    insertSql += id
                    insertSql += ", '" + str(specs[0].text).strip() + "'"
                    insertSql += ", '" + str(specs[1].text).strip() + "'"
                    insertSql += ", '" + str(specs[2].text).strip() + "'"
                    insertSql += ", '" + str(specs[3].text).strip() + "'"
                    insertSql += ", '" + str(specs[4].text).strip() + "'"
                    insertSql += ", '" + str(specs[5].text).strip() + "'"
                    insertSql += ", '" + str(specs[6].text).strip() + "'"
                    insertSql += ", '" + carLink + "'"
                    insertSql += ")"
                    print(insertSql)

                    # INSERT文 実行
                    cur.execute(insertSql)
                    # INSERT をコミット
                    conn.commit()

if __name__ == '__main__':
    main()