import ipaddress
import os
import socket
import struct
import sys

class IP:
    # 受信したバッファの先頭の20バイトをIPヘッダーにマップする構造体を定義
    def __init__(self, buff=None):
        # ここで先頭20バイト取得。Bは1byte unsigned char で　Hは2byte insigned short sはバイト列。4sは4バイトの文字列という意味
        header = struct.unpack('<BBHHHBBH4s4s', buff)
        # 上位ニブルのみver変数に割り当てる。ニブルは4ビット単位のデータ
        # 今回verに割り当てるために4ビット右にシフトしている。こうすることで上位4ビットに0が入り下位4ビットが消えるので結果的に4ビットが取得できる
        self.ver = header[0] >> 4
        # ihlに割り当てるのは下位ニブルを当てたいので0xF(00001111)のANDを取る。
        # そうすると上位4ビットは0となるので消える。下位4ビットは1と比較されるのでそのまま残る
        self.ihl = header[0] & 0xF

        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]
        # IPアドレスを人が読める形に変換して格納
        self.src_address = ipaddress.ip_address(self.src)
        self.dst_address = ipaddress.ip_address(self.dst)
        # プロトコルの定数値を名称にマッピング
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            print('%s No protocol for %s' % (e, self.protocol_num))
            self.protocol= str(self.protocol_num)
    
    def sniff(host):
        if os.name == 'nt':
            socket_protocol = socket.IPPROTO_IP
        else:
            socket_protocol = socket.IPPROTO_ICMP
        
        sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
        sniffer.bind((host, 0))
        sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        if os.name == 'nt':
            sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        
        try:
            while True:
                # パケットの読み込み
                # IP構造体を用いて継続的にパケットを読み取りそれらの情報をパースするロジック
                raw_buffer = sniffer.recvfrom(65535)[0]
                # パースした情報の20バイトを見てIP構造体を作成
                ip_header = IP(raw_buffer[0:20])
                # 出力
                print('Protocol: %s %s -> %s' % (ip_header.protocol, ip_header.src_address, ip_header.dst_address))
        except KeyboardInterrupt:
            if os.name == 'nt':
                sniffer.ioctl(socket.SIO_RCVALL,socket.RCVALL_OFF)
            sys.exit()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = '192.168.242.108'
    IP.sniff(host)