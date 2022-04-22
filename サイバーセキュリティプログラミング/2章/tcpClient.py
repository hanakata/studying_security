# 前提（単純化するため）
# ・接続は常に成功する
# ・サーバは最初にデータを送信することを期待
# ・サーバは常にタイムリーにデータを返してくれる

import socket

target_host = "www.google.co.jp"
target_port = 80
# AF_INFTとSOCK_STREAM)のパラメータを利用してソケットオブジェクトの作成
# AF_INFTはIPv4アドレスやホスト名を使用することを示す
# SOCK_STREAMはTCPクライアントであることを示す
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#サーバへ接続
client.connect((target_host,target_port))
#データの送信（バイト）
client.send(b"GET / HTTP/1.1\r\n\Host: google.co.jp\r\n\r\n")
#データの受信
response = client.recv(4096)

print(response.decode())
client.close()