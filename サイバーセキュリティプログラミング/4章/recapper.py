from email import header
from urllib import response
from pip import main
from scapy.all import TCP, rdpcap
import collections
import os
import re
import sys
import zlib

# 画像ファイルの書き出し先とpcapファイルの読み取りディレクトリの指定
OUTDIR = '/home/kali/pictures'
PCAPS = '/home/kali/Downloads'

# Response変数の定義としてパケットのheaderとpayloadの2つの属性を持つように定義
Response = collections.namedtuple('Response',['header','payload'])

# パケットのヘッダーを取得する処理
def get_header(payload):
    try:
        # 生パケットデータの先頭からキャリッジリターン（CR）とラインフィールド(LF)のセットが2つ連続されるまでを抽出
        header_raw = payload[:payload.index(b'\r\n\r\n')+2]
    except ValueError:
        sys.stdout.write('-')
        sys.stdout.flush()
        # パターンが見つからなければエラーで終わらす
        return None
    try:
        #　発見した場合ペイロードから辞書を作成する
        header = dict(re.findall(r'(?<name>.*?): (?P<value>.*?)\r\n', header_raw.decode()))
        if 'Content-Type' not in header:
            return None
    except:
        return None
    return header

# パレットのコンテンツを取得する処理
def extract_content(Response, content_name='image'):
    try:
        content, content_type = None, None
        # 画像を含むどんなレスポンスでもContent-Typeにはimageが含まれる
        if content_type in Response.header['Content-Type']:
            # スラッシュに続く箇所を変数に抽出することによりヘッダーで指定された実際のコンテンツタイプを取得する
            content_type = Response.header['Content-Type'].split('/')[1]
            # コンテンツ全体を格納
            content = Response.payload[Response.payload.index(b'\r\n\r\n')+4]
        # コンテンツが圧縮されている場合の処理
        if 'Content-Encoding' in Response.header:
            if Response.header['Content-Encooding'] == "gzip":
                content = zlib.decompress(Response.payload, zlib.MAX_WBITS | 16)
            elif Response.header['Content-Encoding'] == "deflate":
                content = zlib.decompress(Response.payload)
    except:
        pass
    return content, content_type

class Recapper:
    # pcapのファイル名でオブジェクトを初期化
    def __init__(self, fname):
        pcap = rdpcap(fname)
        # 各TCPセッションをそれぞれに完全なTCPストリームが格納された辞書に自動的に分ける
        self.sessions = pcap.sessions()
        # pcapファイルから抽出されたレスポンスを格納するためのリスト
        self.response = list()
    # pcapファイルからレスポンスを読み取る
    def get_responses(self):
        # sessions辞書に含まれる複数のセッションの反復処理
        for session in self.sessions:
            payloads = list()
            # 各セッションに含まれる複数のパケットを反復処理
            for packet in self.sessions[session]:
                try:
                    # 同一セッション内で送信ポート、あるいは受信ポートが80であるパケットの場合
                    if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                        if b'\r\n\r\n' in bytes(packet[TCP].payload):
                            payloads.append(b'')
                        # ペイロードを再構築してpayloadsというリスト型の中の一つの変数に格納する
                        payloads[-1] += bytes(packet[TCP].payload)
                except IndexError:
                    # pcap内にTCPパケットが含まれないなどの理由で失敗した場合の例外処理
                    sys.stdout.write('x')
                    sys.stdout.flush()
            # payloadsについて反復処理
            for payload in payloads:
                if payload:
                    # payloadをHTTPヘッダーのパース用関数であり個々のHTTPヘッダーフィールドを辞書形式で抽出できるget_headerに渡す
                    header = get_header(payload)
                    if header is None:
                        continue
                    # Responseをresponsesリストに追加する
                    self.responses.append(Response(header=header, payload=payload))
        print('')
    # レスポンスに含まれる画像をアプロプットディレクトリにファイルとして書き出す
    def write(self, content_name):
        # レスポンスの反復処理
        for i, response in enumerate(self.responses):
            # コンテンツの抽出
            content, content_type = extract_content(response, content_name)
            if content and content_type:
                fname = os.path.join(OUTDIR, f'ex_{i}.{content_type}')
                print(f'Writing {fname}')
                with open(fname, 'wb') as f:
                    # コンテンツの書き込み
                    f.write(content)
if __name__ == '__main__':
    pfile = os.path.join(PCAPS, 'pcap.pcap')
    recapper = Recapper(pfile)
    recapper.get_responses()
    recapper.write('image')