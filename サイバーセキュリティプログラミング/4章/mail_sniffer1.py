from scapy.all import *

# 盗聴した各パケットを受け取るコールバック関数を定義
def pachket_callback(packet):
    print(packet.show())

# フィルターなしですべてのインタフェースを監視するように指示する
def main():
    sniff(prn=pachket_callback, count=1)

if __name__ == '__main__':
    main()