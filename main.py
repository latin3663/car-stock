# -*- coding: utf-8 -*-
from flask import Flask, make_response
import os
from io import StringIO
import csv
import psycopg2

# 定数（環境変数から取得）
DATABASE_URL = os.getenv('DATABASE_URL', None)

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "hello world."


@app.route("/download/csv")
def download():

    f = StringIO()
    writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\n")
    # writer.writerow(['id','username','gender','age','created_at'])

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT * FROM car_stock.stock")
            stockRows = cur.fetchall()

            for row in stockRows:
                writer.writerow([row[0], row[1]])

    res = make_response()
    res.data = f.getvalue()
    res.headers['Content-Type'] = 'text/csv'
    res.headers['Content-Disposition'] = 'attachment; filename='+ "car-stock" +'.csv'
    return res


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)