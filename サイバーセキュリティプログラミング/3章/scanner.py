from ctypes import *
from email import header
import ipaddress
import os
import socket
import struct
import sys
import threading
import time

SUBNET = '192.168.242.0/24'
MESSAGE = 'PYTHONRULES!'

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

def udp_sender():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        for ip in ipaddress.ip_network(SUBNET).hosts():
            sender.sendto(bytes(MESSAGE, 'utf8'), (str(ip), 65212))
class Scanner:
    def __init__(self, host):
        self.host = host
        if os.name == 'nt':
            socket_protocol = socket.IPPROTO_IP
        else:
            socket_protocol = socket.IPPROTO_ICMP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
        self.socket.bind((host, 0))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        if os.name == 'nt':
            self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    def sniff(self):
        host_up = set([f'{str(self.host)} *'])
        try:
            while True:
                raw_buffer = self.socket.recvfrom(65535)[0]
                ip_header = IP(raw_buffer[0:20])
                if ip_header.protocol == "ICMP":
                    offset = ip_header.ihl * 4
                    buf = raw_buffer[offset:offset + 8]
                    icmp_header = ICMP(buf)
                    if icmp_header.code == 3 and icmp_header.type == 3:
                        if ipaddress.ip_address(icmp_header.src_address) in ipaddress.IPv4Network(SUBNET):
                            if raw_buffer[len(raw_buffer) - len(MESSAGE):] == bytes(MESSAGE, 'utf8'):
                                tgt = str(ip_header.src_address)
                                if tgt != self.host and tgt not in host_up:
                                    host_up.add(str(ip_header.src_address))
                                    print(f'Host Up: {tgt}')
        except KeyboardInterrupt:
            if os.name == 'nt':
                self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            print('\nUser Interrupted')
            if host_up:
                print(f'\n\nSummary: Hosts up on {SUBNET}')
            for host in sorted(host_up):
                print(f'{host}')
            print('')
            sys.exit()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = '192.168.242.108'
    s = Scanner(host)
    time.sleep(5)
    t = threading.Thread(target=udp_sender)
    t.start()
    s.sniff()