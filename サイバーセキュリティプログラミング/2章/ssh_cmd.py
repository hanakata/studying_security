import paramiko

# ssh_command関数を作成しSSHサーバへの接続を行い単一のコマンド実行
def ssh_command(ip, port, user, passwd, cmd):
    client = paramiko.SSHClient()
    # 接続先のSSHサーバのSSH鍵を受け入れるようにポリシーを設定し接続を行う
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    # 接続に成功するとssh_command関数の呼び出しで渡したコマンド実行を行う
    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()
    if output:
        print('--- Output ---')
        for line in output:
            print(line.strip())

if __name__ == '__main__':
    # mainでgetpassを利用する
    import getpass
    user = input('Username: ')
    password = getpass.getpass()

    ip = input('Enter server IP: ') or '192.168.1.203'
    port = input('Enter port or <CR>: ') or '2222'
    cmd = input('Enter command or <CR>: ') or 'id'
    ssh_command(ip, port, user, password, cmd)