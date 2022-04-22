# 前提（単純化するため）
# ・接続は常に成功する
# ・サーバは最初にデータを送信することを期待
# ・サーバは常にタイムリーにデータを返してくれる

import socket

target_host = "127.0.0.1"
target_port = 9997
# AF_INFTとSOCK_STREAM)のパラメータを利用してソケットオブジェクトの作成
# AF_INFTはIPv4アドレスやホスト名を使用することを示す
# SOCK_DGRAMはUDPクライアントであることを示す
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#データの送信
client.sendto(b"AAABBBCCC", (target_host, target_port))
#データの受信
data, address = client.recvfrom(4096)

print(data.decode('utf-8'))
print(address)
client.close()