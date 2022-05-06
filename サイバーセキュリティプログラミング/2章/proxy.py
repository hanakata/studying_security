from http import client
import sys
import socket
import threading
from tkinter.tix import MAIN

from sympy import li

# HEX_FILTERに代入する文字列を作成。
# データがASCIIの印字可能な文字の場合はそのまま保持しそうでない場合はドットに置き換える変換テーブル
HEX_FILTER = ''.join([(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])

def hexdump(src, length=16, show=True):
    # バイトデータを受け取った場合は文字列にデコードする
    if isinstance(src, bytes):
        src = src.decode()
    # 文字列を格納するための新しい配列resultを作成する
    results = list()
    for i in range(0, len(src), length):
        # ダンプするデータの一部を取り出し変数wordに代入する
        word = str(src[i:i+length])

        # 組み込み関数のtranslateを使用し変換テーブルGEX_FILTERを使用して対応する文字列に置き換える
        # 置き換えた文字列を変数printableに代入する
        printable = word.translate(HEX_FILTER)
        # 生データを16進数で表現したものを代入
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        hexwidth = length*3
        # インデックスの16進数表記、データの16進ダンプ、変換テーブルによって置き換えられた文字列が格納される
        results.append(f'{i:04x}  {hexa:<{hexwidth}}  {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results

def receive_from(connection):
    buffer = b''
    # タイムアウトを5秒に設定
    connection.settimeout(5)
    try:
        while True:
            # データを受信しなくなるかタイムアウトするまでbufferにレスポンスデータを読み込む
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except:
        pass
    # 呼び出し元にbufferを戻す
    return buffer

def request_handler(buffer):
    return buffer

def response_handler(buffer):
    return buffer

def proxy_handler(client_socket, remote_host, remote_port,receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # リモートホストに接続する
    remote_socket.connect((remote_host, remote_port))
    # メインの繰り返し処理に入る前に最初にリモート側へデータを要求する必要がないことを確認する
    if receive_first:
        
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)
            # repsponse_handlerに出力を渡し受信したバッファをローカルクライアントに送信する
            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[==>] Sent to local.")
    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print("[<==] Received %d bytes from local." % len(local_buffer))
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote")
        
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[==>] Sent to local")
        # リモートとローカルのどちらの側にも送信するデータがなくなると双方のソケットを閉じ繰り返し処理を終える
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections")
            break
def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    # ソケットを作成
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # ローカルホストにバインドして接続を待ち受ける
        server.bind((local_host, local_port))
    except Exception as e:
        print('problem on bind: %r' % e)
        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions")
        sys.exit(0)
    
    print("[*] Listening on %s:%d" % (local_host,local_port))
    server.listen(5)
    # メインの繰り返し処理
    while True:
        client_socket, addr = server.accept()
        # 接続情報の出力
        line = "> Received incoming connection from %s:%d" % (addr[0], addr[1])
        print(line)
        # リモートホストとの接続を行うスレッドの開始
        # 新しい接続要求を受け取ると新しいスレッドを起動してproxy_handlerを私双方向からのデータの送受信をすべて担当させる
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host,remote_port,receive_first)
        )
        proxy_thread.start()

def main():
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end='')
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)

    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]
    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
    
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

if __name__ == '__main__':
    main()