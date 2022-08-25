import queue
from tkinter.messagebox import NO
import requests
import sys
import threading

AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
EXTENSIONS = ['.php', '.bak', '.orig', '.inc']
TARGET = "http://testphp.vulnweb.com"
THREADS = 50
WORDLIST = "DLしてきた攻撃対象単語ファイル"

# 単語のキューオブジェクトを返す関数
def get_words(resume=None):
    # この関数はget_words関数から常に呼び出されるため関数内関数の形を取る
    def extend_words(word):
        if "." in word:
            words.put(f'/{word}')
        else:
            words.put(f'/{word}')

        for extension in EXTENSIONS:
            words.put(f'{word}{extension}')
    with open(WORDLIST) as f:
        # 単語リストのファイル読み込み
        raw_words = f.read()

    found_resume = False
    words = queue.Queue()
    for word in raw_words.split():
        # 前回の辞書攻撃で試した最後のパスをresumeという引数で受け取る
        if resume is not None:
            if found_resume:
                extend_words(word)
            elif word == resume:
                found_resume = True
                print(f'Resuming wordlist from: {resume}')
        else:
            print(word)
            extend_words(word)
    # 辞書攻撃の関数で使用される単語群が格納されたQueueを返す
    return words

def dir_bruter(words):
    # User-Agentを定義
    headers = {'User-Agent': AGENT}
    while not words.empty():
        # 攻撃対象のURLを生成
        url = f'{TARGET}{words.get()}'
        try:
            r = requests.get(url, headers=headers)
        except:
            # connection エラー
            sys.stderr.write('X');sys.stderr.flush()
            continue
        if r.status_code == 200:
            # 200であればURL表示
            print(f'\nSuccess ({r.status_code}: {url}')
        elif r.status_code == 404:
            sys.stderr.write('.');sys.stderr.flush()
        else:
            print(f'{r.status_code} => {url}')

if __name__ == '__main__':
    words = get_words()
    print('Press return to continue.')
    sys.stdin.readline()
    for _ in range(THREADS):
        t = threading.Thread(target=dir_bruter, args=(words,))
        t.start