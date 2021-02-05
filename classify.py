from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from pathlib import Path
import os
import numpy as np
#import argparse
import imutils
import pickle
import cv2
from PIL import Image, ImageDraw, ImageFont

def _cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    #if (isinstance(img, np.ndarray)):  #判斷是否OpenCV圖片類型
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(
        "font/simsun.ttc", textSize, encoding="utf-8")
    draw.text((left, top), text, textColor, font=fontText)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

def _classify(img_path, model_path, labelbin_path):
    """
    # 命令列參數設定
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--model", required=True,
    	help="path to trained model model")
    ap.add_argument("-l", "--labelbin", required=True,
    	help="path to label binarizer")
    ap.add_argument("-i", "--image", required=True,
    	help="path to input image")
    args = vars(ap.parse_args())
    """
    
    # 載入圖片
    image = cv2.imread(str(img_path))
    output = imutils.resize(image, width=400)
    
    # 輸入圖片預處理
    image = cv2.resize(image, (96, 96))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)

    # 載入 CNN 分類器模型 和 二值化的標籤
    print("[INFO] 正在載入神經網路模型")
    model = load_model(model_path)
    
    #with open(labelbin_path, "rb") as fp:
    #    mlb = pickle.loads(fp)
    mlb = pickle.loads(open(labelbin_path, "rb").read())
    
    # 對輸入圖片做辨識(預測)，並將各標籤"機率"遞減排序，取前 2 高的索引暫時記錄在 indices 
    # 若模型預測準確，前 2 項應為: XX顏色 和 XX服飾種類
    print("[INFO] 正在辨識圖片")
    probs = model.predict(image)[0]
    indices = np.argsort(probs)[::-1][:2]

    # 將前兩項預測結果(只能是顏色/服飾分類其一)呈現在圖表左上角
    # i:[0,1] 用來定位 預測結果 的顯示位置
    # label | i.e., 預測結果: 準確率% | e.g., 襯衫類: 97.23%
    '''for i, cat_idx in enumerate(indices):
        category = mlb.classes_[cat_idx]
        prob = round(probs[cat_idx]*100, 2)
        #label = f"{category}: {prob}%"
        label = ""
        cv2.putText(output, label, (10, (i * 30) + 25), 
    		cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)'''
    
    # 轉為PIL圖片以在圖片中顯示中文結果標籤 | cv向量圖 => PIL向量圖 => cv向量圖 
    label = ""
    for i, cat_idx in enumerate(indices):
        category = mlb.classes_[cat_idx]
        prob = round(probs[cat_idx]*100, 2)
        label += f"{category}: {prob}%\n"
    # "cyan" <- output[0:45, 0:155]
    # cyan: rgb(0,255,255)
    # cyan: rgb(165, 222, 228)
    
    text_color = (0, 0, 0) # 黑
    #text_bg_color = (247, 92, 47) # 緋紅
    text_bg_color = (255, 150, 0) # 橘
    for h in range(45):
        for w in range(155):
            output.itemset((h,w,0), text_bg_color[-1]) # B
            output.itemset((h,w,1), text_bg_color[1])   # G
            output.itemset((h,w,2), text_bg_color[0])   # R
    pil_image = _cv2ImgAddText(output, label, 0, 0, text_color, 22)
    
    # 印出每個標籤的估計機率
    #for label, p in zip(mlb.classes_, probs):
    #	print(f"{label}: {round(p*100, 2)}%")
    #print(*(f"{round(prob*100, 2)}%" for prob in sorted(probs, reverse=True)[:5]))
    for top_label, top_p in zip(_sort_list1_by_list2(mlb.classes_, probs), sorted(probs, reverse=True)[:5]):
        print(f"{top_label}: {round(top_p*100, 2)}%")
    # 顯示圖片
    #cv2.imshow("辨識結果", output)
    cv2.imshow("辨識結果", pil_image)
    cv2.waitKey(0)

def _sort_list1_by_list2(list1, list2):
    #list1 = ["a", "b", "c"]
    #list2 = [2, 3, 1]
    zipped_lists = zip(list2, list1)
    sorted_zipped_lists = sorted(zipped_lists, reverse=True) # 遞減
    sorted_list1 = [element for _, element in sorted_zipped_lists]
    #print(sorted_list1)
    return sorted_list1

def classify_demo(img_path):
    base_result_dir = "result/002_0126"
    model_path = Path(base_result_dir) / Path("fashion.model")
    labelbin_path = Path(base_result_dir) / Path("mlb.pickle")
    
    if img_path.exists() and model_path.exists() and labelbin_path.exists():
        _classify(img_path, model_path, labelbin_path)
    else:
        if not img_path.exists():
            print(f"[WARNING] 找不到圖片路徑: {img_path}")
        if not model_path.exists():
            print(f"[WARNING] 找不到模型路徑: {model_path}")
        if not labelbin_path.exists():
            print(f"[WARNING] 找不到二值化標籤路徑: {labelbin_path}")
        
if __name__ == "__main__":
    #img_list = ["1.jpg", "2.jpeg", "3.jpg"]
    img_list = [f for f in os.listdir("dataset/test_data_to_classify") if not os.path.isdir(f)]
    #print(img_list)
    # "dataset/test_data_to_classify"
    
    test_image = img_list[9]
    img_path = Path("dataset/test_data_to_classify") / Path(test_image)
    classify_demo(img_path)
    