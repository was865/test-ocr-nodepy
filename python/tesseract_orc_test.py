from PIL import Image, ImageEnhance
import pyocr
import pyocr.builders
from IPython.display import Image as ipy_Image, display
import os
import cv2
import numpy as np

# Nodejs用
import sys, json, pickle
import pandas as pd
import codecs
import requests
import tempfile
import base64
import io
from imageio import imread

jsonData = sys.stdin.readline()  #  ①データはこうやって読み込むらしいがテキスト形式になっているので注意！
json_dict = json.loads(jsonData)

err_msg = ""


def imshow(img):
    """ndarray 配列をインラインで Notebook 上に表示する。"""
    ret, encoded = cv2.imencode(".png", img)
    display(ipy_Image(encoded))


def getStdThrsh(img, Blocksize):
    stds = []
    for y in range(0, img.shape[0], Blocksize):
        for x in range(0, img.shape[1], Blocksize):
            pimg = img[y : y + Blocksize, x : x + Blocksize]
            std = np.std(pimg)
            stds.append(std)

    hist = np.histogram(stds, bins=64)
    peaki = np.argmax(hist[0])

    # plt.hist( stds, bins=64 )
    # plt.show()

    slim = 6.0
    for n in range(peaki, len(hist[0]) - 1):
        if hist[0][n] < hist[0][n + 1]:
            slim = hist[1][n + 1]
            break

    if slim > 6.0:
        slim = 6.0

    return slim


def getOutputName(title, slim):
    return title + "_s{:04.2f}.jpg".format(slim)


def sharpenImg(img):

    # 文字と白地の区別をつける
    try:
        # Testimagefile = imgfile
        # TestimageTitle = Testimagefile.split('.')[0]
        Blocksize = 64

        # bookimg = cv2.imread( Testimagefile )
        bookimg = img
        img_gray = cv2.cvtColor(bookimg, cv2.COLOR_BGR2GRAY)
        # img_gray = img

        slim = getStdThrsh(img_gray, Blocksize)
        yimgs = []
        for y in range(0, img_gray.shape[0], Blocksize):
            s = ""
            ximgs = []
            for x in range(0, img_gray.shape[1], Blocksize):
                pimg = img_gray[y : y + Blocksize, x : x + Blocksize]
                std = np.std(pimg)

                if std < slim:
                    s = s + "B"
                    ximg = np.zeros(pimg.shape) + 255
                else:
                    s = s + "_"
                    lut = np.zeros(256)
                    white = int(np.median(pimg))
                    black = int(white / 2)
                    cnt = int(white - black)
                    for n in range(cnt):
                        lut[black + n] = int(256 * n / cnt)
                    for n in range(white, 256):
                        lut[n] = 255
                    ximg = cv2.LUT(pimg, lut)
                ximgs.append(ximg)
            #         print( "{:4d} {:s}".format( y, s ) )
            yimgs.append(cv2.hconcat(ximgs))

        outimage = cv2.vconcat(yimgs)
        cv2.imwrite(getOutputName("TestimageTitle", slim), outimage)
        outimage = cv2.imread(getOutputName("TestimageTitle", slim), 0)
        os.remove(getOutputName("TestimageTitle", slim))
        # cv2.imwrite(getOutputName(TestimageTitle, slim), outimage)
        return outimage
    except Exception as e:
        err_msg = err_msg + "文字白地分離化処理、失敗しました。"


def img2str(img, is_del_line=False, is_sharpen_img=True, is_tate=False):

    # Pah設定
    TESSERACT_PATH = "C:\\Program Files\\Tesseract-OCR"  # インストールしたTesseract-OCRのpath
    TESSDATA_PATH = "C:\\Program Files\\Tesseract-OCR\\tessdata"  # tessdataのpath

    os.environ["PATH"] += os.pathsep + TESSERACT_PATH
    os.environ["TESSDATA_PREFIX"] = TESSDATA_PATH

    # OCRエンジン取得
    tools = pyocr.get_available_tools()
    tool = tools[0]

    # OCRの設定 ※tesseract_layout=6が精度には重要。デフォルトは3
    if is_tate:
        builder = pyocr.builders.TextBuilder(tesseract_layout=5)
    else:
        builder = pyocr.builders.TextBuilder(tesseract_layout=6)

    # 画像取得
    # [option] 必要に応じて画像処理 文字と白地の区別をつける
    if is_sharpen_img:
        img = sharpenImg(img)
        # print("sharpen処理済み：")
        # print("--------------------------------------------------------------------------------")
        # imshow(img)
        # print("--------------------------------------------------------------------------------")
    # else:
    #     img = cv2.imread(file_path, 0)
    # print("sharpen処理なし：")
    # print("--------------------------------------------------------------------------------")
    # imshow(img)
    # print("--------------------------------------------------------------------------------")

    # 明るさ・コントラスト操作
    #     alpha = 0.8 # コントラスト項目
    #     beta = 0.0    # 明るさ項目
    #     img = cv2.convertScaleAbs(img,alpha = alpha,beta = beta)
    #     print("コンストラクタ:", alpha, "  明るさ:", beta)
    #     imshow(img)

    # [option] 必要に応じて画像処理 線を消す
    if is_del_line:
        img = delete_line(img)
        cv2.imwrite("sample_edited.png", img)
        # print("線を消し済み：")
        # print("--------------------------------------------------------------------------------")
        # imshow(img)
        # print("--------------------------------------------------------------------------------")

    img = Image.fromarray(img)

    # 画像からOCRで日本語を読んで、文字列として取り出す
    if is_tate:
        # 縦読みの場合
        txt_pyocr = tool.image_to_string(img, lang="jpn_vert", builder=builder)
    else:
        txt_pyocr = tool.image_to_string(img, lang="jpn", builder=builder)

    # 半角スペースを消す ※読みやすくするため
    # txt_pyocr = txt_pyocr.replace(' ', '')

    return txt_pyocr


def delete_line(img):

    # 必要に応じて画像処理 線を消す
    img_temp = img
    try:
        _, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
        img = cv2.bitwise_not(img)
        label = cv2.connectedComponentsWithStats(img)
        data = np.delete(label[2], 0, 0)
        new_image = np.zeros((img.shape[0], img.shape[1])) + 255
        for i in range(label[0] - 1):
            if 0 < data[i][4] < 1000:
                new_image = np.where(label[1] == i + 1, 0, new_image)

        return new_image
    except Exception as e:
        err_msg = err_msg + "線を消す処理、失敗しました。"
        return img_temp


def imread_web(url, is_gray):
    # 画像をリクエストする
    res = requests.get(url)
    img = None
    # Tempfileを作成して即読み込む
    fp = tempfile.NamedTemporaryFile(dir="./", delete=False)
    fp.write(res.content)
    fp.close()
    if is_gray:
        img = cv2.imread(fp.name, 0)  #  grayで読み込む
    else:
        img = cv2.imread(fp.name)
    os.remove(fp.name)
    return img


# OCR検知
img = None

is_gray = False
if json_dict["is_del_line"] == True and json_dict["is_sharpen_img"] == False:
    is_gray = True

img_exist = True
try:
    img = imread_web(json_dict["url"], is_gray)
    img.shape
except:
    img_exist = False

if json_dict["img_base64"]:
    data = json_dict["img_base64"]
    string = data[data.find("base64") + 7 :]  # ****
    img = imread(io.BytesIO(base64.b64decode(string)))  # RGB
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # cv2のBGR
    img_exist = True

if img_exist:
    txt_pyocr = img2str(
        img,
        is_del_line=json_dict["is_del_line"],
        is_sharpen_img=json_dict["is_sharpen_img"],
        is_tate=json_dict["is_tate"],
    )
    # 無理矢理jsonに入れる
    jsonResult = (
        '{"txt_pyocr": "'
        + txt_pyocr.replace("\n", "<br>").replace('"', "").replace("\\", "")
        + '", "err_msg": "'
        + err_msg
        + '"}'
    )
else:
    err_msg = err_msg + "指定するURLが正しくありません。"
    jsonResult = '{"txt_pyocr": "", "err_msg": "' + err_msg + '"}'

# js側に渡す
print(jsonResult)
