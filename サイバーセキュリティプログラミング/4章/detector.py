from cmath import rect
import cv2
import os

ROOT = '/home/kali/pictures'
FACES = '/home/kali/faces'
TRAIN = '/home/kali/training'

def detect(srcdir=ROOT, tgtdir=FACES, train_dir=TRAIN):
    for fname in os.listdir(srcdir):
        # srcdir内のjpegファイルを対象にして反復処理
        if not fname.upper().endswith('.JPEG'):
            continue
        fullname = os.path.join(srcdir, fname)
        newname = os.path.join(tgtdir, fname)
        # opencvを用いて画像読み込み
        img = cv2.imread(fullname)
        if img is None:
            continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            training = os.path.join(train_dir, 'haarcascade_frontalface_alt.xml')
            # 分類器となるxmlファイルを読み込んで顔検出用オブジェクト作成
            cascade = cv2.CascadeClassfier(training)
            rects = cascade.detectMultiScale(gray, 1.3, 5)
            try:
                #画像中に顔が検出された場合の処理
                if rects.any():
                    print('Got a face')
                    rects[:, 2:] += rects[:, :2]
            except AttributeError:
                print(f'No faces found in {fname}.')
                continue
            for x1, y1, x2, y2 in rects:
                # 緑色の枠を追加
                cv2.rectamgle(img, (x1,y1), (x2,y2), ('127, 255, 0'), 2)
            # 画像書き出し
            cv2.imwrite(newname, img)
if __name__ == '__main__':
    detect()