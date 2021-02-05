# USAGE
# python train.py --dataset dataset --model fashion.model --labelbin mlb.pickle

# set the matplotlib backend so figures can be saved in the background
import matplotlib
matplotlib.use("Agg")

from model.smaller_vgg_net import SmallerVGGNet
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import img_to_array
import tensorflow as tf
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from imutils import paths
import numpy as np
import argparse
import random
import pickle
import cv2
import os

def train():
    # 建立命令列程式
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dataset", required=True,
     help="path to input dataset (i.e., directory of images)")
    ap.add_argument("-m", "--model", required=True,
     help="path to output model")
    ap.add_argument("-l", "--labelbin", required=True,
     help="path to output label binarizer")
    ap.add_argument("-p", "--plot", type=str, default="plot.png",
     help="path to output accuracy/loss plot")
    args = vars(ap.parse_args())

    # 初始化參數
    '''
    INIT_LR:     initial learning rate
    BS:          Batch Size
    IMG_DIMS:    讀入圖片尺寸
    '''
    EPOCHS = 75
    INIT_LR = 1e-3
    BS = 32
    IMG_DIMS = (96, 96, 3) # (height, width, depth)
    tf.compat.v1.disable_eager_execution()

    # 從 dataset 命令參數的圖片路徑載入圖片
    print("[INFO] 正在載入圖片...")
    img_paths = sorted(list(paths.list_images(args["dataset"])))
    random.seed(42)
    random.shuffle(img_paths)
    
    # 初始化 圖片資料、標籤 串列
    data = list()
    labels = list()

    # [預處理] 遍歷所有圖片，對所有圖片(feature)和所屬標籤(label)做預處理
    # (1) 讀取所有圖片和標籤
    for img_path in img_paths:
        # 載入圖片，做預處理後存入 data 串列
        img = cv2.imread(img_path)
        
        # [USAGE] cv2. resize(img, (customized_width, customized_height))
        img = cv2.resize(img, (IMG_DIMS[1], IMG_DIMS[0]))
        img = img_to_array(img)
        data.append(img)
        
        # 抽取出每張圖片的標籤(=>'(顏色)_(分類)')並加入 labels 串列
        lbl = img_path.split(os.path.sep)[-2].split("_")[1:]
        labels.append(lbl)

    # (2) 特徵(圖片)縮放至 [0, 1] 區間
    data = np.array(data, dtype="float") / 255.0
    labels = np.array(labels) # list => numpy array
    print(f"[INFO] 共尋獲 {len(img_paths)} 張圖片")
    print(f"資料大小: {round(data.nbytes/(1024*1024), 2)} MB")

    # (3) 將文字標籤二值化為數值 (利用 sklearn 的 MultiLabelBinarizer)
    mlb = MultiLabelBinarizer()
    labels = mlb.fit_transform(labels)
    print("[INFO] 服飾分類標籤:")
    print(*(f"({i+1}) {label}" for i, label in enumerate(mlb.classes_)))
    
    # [訓練集/測試集拆分] 80%: 訓練集 / 20% 測試集
    (trainX, testX, trainY, testY) = train_test_split(data, labels, test_size=0.2, random_state=42)

    # 建構圖片生成器(image generator)
    aug = ImageDataGenerator(rotation_range=25, width_shift_range=0.1,
           height_shift_range=0.1, shear_range=0.2, zoom_range=0.2,
           horizontal_flip=True, fill_mode="nearest")
    
    # 為了做"多標籤分類"(非多元分類)，輸出層的 activation func. 選擇用 'sigmoid' 而非 'softmax' 
    print("[INFO] 正在建立模型")
    model = SmallerVGGNet.build(width=IMG_DIMS[1], height=IMG_DIMS[0],
                                depth=IMG_DIMS[2], n_classes=len(mlb.classes_),
                                output_activation="sigmoid")
    

    # 設定優化器 (SGD 也足夠了)
    optimizer_ = Adam(lr=INIT_LR, decay=INIT_LR / EPOCHS)

    # compile the model using binary cross-entropy rather than
    # categorical cross-entropy -- this may seem counterintuitive for
    # multi-label classification, but keep in mind that the goal here
    # is to treat each output label as an independent Bernoulli
    # distribution
    model.compile(loss="binary_crossentropy", optimizer=optimizer_,
                  metrics=["accuracy"])

    # 開始訓練神經網路
    print("[INFO] 正在訓練神經網路")
    training_history = model.fit(x=aug.flow(trainX, trainY, batch_size=BS),
                                 validation_data=(testX, testY),
                                 steps_per_epoch=len(trainX) // BS,
                                 epochs=EPOCHS, verbose=1)
    print("[INFO] 訓練結束！")

    # 儲存(serializing) 訓練好的模型到本地
    print("[INFO] 正在儲存模型")
    model.save(args["model"], save_format="h5")

    # 儲存(serializing) 數值化的標籤到本地
    print("[INFO] 正在儲存數值化的標籤")
    with open(args["labelbin"], "wb") as fp:
        fp.write(pickle.dumps(mlb))

    # 繪製出: 訓練過程的 損失(loss) 及 準確率(accuracy)
    plt.style.use("ggplot")
    plt.figure()
    plt.plot(np.arange(0, EPOCHS), training_history.training_historyory["loss"], label="train_loss")
    plt.plot(np.arange(0, EPOCHS), training_history.training_historyory["val_loss"], label="val_loss")
    plt.plot(np.arange(0, EPOCHS), training_history.history["acc"], label="train_acc")
    plt.plot(np.arange(0, EPOCHS), training_history.training_historyory["val_acc"], label="val_acc")
    plt.title("Training Loss and Accuracy")
    plt.xlabel("Epoch #")
    plt.ylabel("Loss/Accuracy")
    plt.legend(loc="upper left")
    plt.savefig(args["plot"])