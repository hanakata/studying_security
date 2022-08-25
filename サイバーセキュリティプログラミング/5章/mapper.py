import contextlib
from importlib.resources import path
import os
import queue
from re import U
from unittest.mock import patch
import requests
import sys
import threading
import time

FILTERD = [".jpg", ".gif", ".png", ".css"]
# ターゲットのURLを入力する
TARGET = "target url"
THREADS = 10

# 実際にリモートサーバでアクセスできたURLを溜めるもの
answers = queue.Queue()
# ターゲットのWebサイトでアクセスを試行するファイルのリストを溜めるためのQueueオブジェクト
web_paths = queue.Queue()

def gather_paths():
    # Webアプリケーションディレクトリ内すべてのファイル、ディレクトリを再帰的に探索
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERD:
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]
            print(path)
            web_paths.put(path)

# コンテキストマネージャ
@contextlib.contextmanager
# コードを違うディレクトリで実行することが可能
def chdir(path):
    """
    On enter, change directory to specified path.
    On exit, change directory back to original.
    """
    this_dir = os.getcwd()
    os.chdir(path)
    try:
        # コンテキストを初期化してgather_pathsにコントロールを戻す
        yield
    finally:
        # 元のディレクトリに戻す
        os.chdir(this_dir)

def test_remote():
    # web_paths変数のキューが空になるまでループ
    while not web_paths.empty():
        # キューからパスを取り出す
        path = web_paths.get()
        url = f'{TARGET}{path}'
        time.sleep(2)
        r = requests.get(url)
        if r.status_code == 200:
            # レスポンスが200の場合URLをanswerキューに入れて+を出力
            answers.put(url)
            sys.stdout.write('+')
        else:
            sys.stdout.write('×')
        sys.stdout.flush()

def run():
    mythreads = list()
    # 定義された分スレッドを起動
    for i in range(THREADS):
        print(f'Spawning thread {i}')
        # それぞれのスレッドにtest_remoteを実行させる
        t = threading.Thread(target=test_remote)
        mythreads.append(t)
        t.start()
    for thread in mythreads:
        thread.join()

if __name__ == '__main__':
    with chdir("/home/kali/Downloads/wordpress"):
        gather_paths()
    input('press return to continue')
    run()
    with open('myanswers.txt', 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
        print('done')