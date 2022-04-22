import socket
import threading

IP = '0.0.0.0'
PORT = 9998

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 待ち受けさせたいIPアドレスとポートを指定
    server.bind((IP, PORT))
    # 最大接続数を5
    server.listen(5)
    print(f'[*] listening on {IP}: {PORT}')

    # 接続がくるまでループ
    while True:
        # client変数にクライアントのソケット、address変数にリモート接続の詳細を受け取る
        client, address = server.accept()
        print(f'[*] Accepted connection from {address[0]}:{address[1]}')
        # handle_client関数を私用するスレッドオブジェクトを作成し引数としてクライアントソケットオブジェクトを渡す
        client_handler = threading.Thread(target=handle_client, args=(client,))
        # この時点でサーバの見えんの繰り返し処理が別の接続を処理できるようになる
        client_handler.start()

def handle_client(client_socket):
    with client_socket as sock:
        request = sock.recv(1024)
        # バイトでリクエストが来る場合はdecodeが出来ないのでdecodeは外すべき
        print(f'[*] Received: {request.decode("utf-8")}')
        sock.send(b'ACK')

if __name__ == '__main__':
    main()