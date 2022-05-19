from ctypes import *
from email import header
import ipaddress
import os
import socket
import struct
import sys

class IP(Structure):
    # 取得したパケット用の構造体
    _fields_ = [
        ("ver",             c_ubyte, 4),
        ("ihl",             c_ubyte, 4),
        ("tos",             c_ubyte, 8),
        ("len",             c_ushort, 16),
        ("id",              c_ushort, 16),
        ("offset",          c_ushort, 16),
        ("ttl",             c_ubyte, 8),
        ("protocol_num",    c_ubyte, 8),
        ("sum",             c_ushort, 16),
        ("src",             c_uint32, 32),
        ("dst",             c_uint32, 32)
    ]

    def __new__(cls, socket_buffer=None):
        # 入力バッファを構造体に格納
        return cls.from_buffer_copy(socket_buffer)
    # 受信したバッファの先頭の20バイトをIPヘッダーにマップする構造体を定義
    def __init__(self, socket_buffer=None):
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))
        # プロトコルの定数値を名称にマッピング
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            print('%s No protocol for %s' % (e, self.protocol_num))
            self.protocol= str(self.protocol_num)
# ICMP構造体作成
class ICMP:
    def __init__(self, buff):
        header = struct.unpack('<BBHHH', buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]

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
            # ヘッダーを確認してICMPパケットの受信を確認したときの処理
            if ip_header.protocol == 'ICMP':
                print('Protocol: %s %s -> %s' % (ip_header.protocol, ip_header.src_address, ip_header.dst_address))
                print(f'Version: {ip_header.ver}')
                print(f'Header Length: {ip_header.ihl} TTL: {ip_header.ttl}')
                # ICMP構造体のバッファを作成した後そのタイプとコードのフィールドを作成
                # このフィールドはIPへっだーに含まれる32ビットワード（4バイトを1単位とする情報量の単位）の数をしめす。
                # そのためこのフィールドを4倍することでIPヘッダーのサイズを知ることができて、かつこのサイズから次のネットワークレイヤーの開始位置が分かる
                offset = ip_header.ihl * 4
                buf = raw_buffer[offset:offset + 8]
                icmp_header = ICMP(buf)
                print('ICMP -> Type: %s Code: %s\n' % (icmp_header.type, icmp_header.code))

    except KeyboardInterrupt:
        if os.name == 'nt':
            sniffer.ioctl(socket.SIO_RCVALL,socket.RCVALL_OFF)
        sys.exit()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = '192.168.242.108'
    sniff(host)