# USAGE
# python clothing_image_searcher.py --index n
# (index: n in range of [0, 143])

from requests import exceptions
import argparse
import requests
#from PIL import Image
#import PIL
#import cv2
#import os
from pathlib import Path
import time

# 顏色: 如紅色太偏橙色 可直接刪除 => 省時、避免錯誤歸類
# 目標: 每個分類夾有 350~400 張圖
# 為做比較好的顏色區隔(與相近顏色，只取明顯是該顏色的data)
# 有多張人像、背景太複雜的，可直接刪除，或手工去背、截圖
# P.S. 除英文外，搜尋其他歐洲語言(如:法文、波蘭文等)等
# 會有該國流行服飾，有時候意外地很多需要的服飾資料
# 日韓文搜到的幾乎都是明星，簡體字/繁中資料比較少

def _call_BingAPI_to_image_search(search_term, BATCH_SIZE, 
                                  SEARCH_URL, headers,
                                  MAX_RESULTS, args, 
                                  EXCEPTIONS, color_cat_path,
                                  is_idx_specified,
                                  color_cat_idx=None):
    
    params = {"q": search_term, "offset": 0, "count": BATCH_SIZE}

    # 發送第一個請求以探測可用資料的資訊
    print(f"[INFO] 利用 Bing-Search-v7 API 搜尋有關 '{search_term}' 的圖片")
    print("[INFO] (1) 正在發送第一個請求以探測可用資料的資訊: ")
    response = requests.get(SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()
    
    # 抓出 response 的 json 以獲取 '至多能下載多少圖片' (json key: "totalEstimatedMatches")
    # 若超過自訂上限 MAX_RESULTS 則限制最大下載資料筆數為 MAX_RESULTS
    
    #search_results = response.json()
    #if search_results["totalEstimatedMatches"]:
    #    estimated_result_num = min(search_results["totalEstimatedMatches"], MAX_RESULTS)
    #else:
    estimated_result_num = 250
    print(f"[INFO] 查詢圖片關鍵字: '{search_term}'\n圖片預計下載資料筆數: {estimated_result_num}")
    
    # 初始化目前'已下載圖片資料筆數'為 0
    # => 改為讀取 /dataset/分類資料夾 下的圖片數量
    image_count = -1
    if Path.exists(color_cat_path):
        tmp_img_amount = len([fp for fp in Path(color_cat_path).iterdir()])
        image_count = tmp_img_amount
    else:
        print("[WARNING] 錯誤！ 無法寫入圖片 (遺失存圖檔路徑，無法讀取/dataset/分類資料夾 下的圖片數量)")
        print("          請檢查程式: 第 53 行附近")
    time_count = 0
    if image_count >= 0:
        # 利用 Bing Search v7 API 逐一下載圖片
        # 並透過 offset 紀錄當前下載進度 及 作為發送請求的參數
        for offset in range(0, estimated_result_num, BATCH_SIZE):
            print(f"[INFO] 正在發送獲取圖片請求 | 進度: {offset}-{offset+BATCH_SIZE} / {estimated_result_num} ({(offset+BATCH_SIZE)*100/estimated_result_num} %)")
            params["offset"] = offset # 指出是第幾批圖片
            response = requests.get(SEARCH_URL, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            print(f"[INFO] 正在儲存圖片 | 進度: {offset}-{offset+BATCH_SIZE} / {estimated_result_num} ({(offset+BATCH_SIZE)*100/estimated_result_num} %)")
            
            for v in results["value"]:
                img_link = v["contentUrl"]
                print(f"[INFO] 圖片網址: {img_link}")
                # extension: 圖片副檔名(含'.') | e.g., ".jpg",".png"
                tmp = img_link.split("/")[-1]
                if "." in tmp:
                    extension = tmp[tmp.rfind("."):]
                else:   
                    extension = ".png"
                    img_link += extension
                print(f"[INFO] 圖片副檔名: {extension}")
                
                try:
                    r = requests.get(img_link, timeout=30)
                    img_file_name = str(image_count).zfill(8)
                    img_save_path = Path(color_cat_path) / Path(img_file_name + extension)
                    with open(img_save_path, "wb") as fp:
                        fp.write(r.content)
                    
                except Exception as e:
                    if e in EXCEPTIONS:
                        print(f"[WARNING] 無法下載圖片: {img_link}")
                        continue
                    else:
                        print("[WARNING] 未知的錯誤:\n" + str(e))
                        continue
                
                else: # 若圖片下載成功
                    print(f"[INFO] 圖片{img_file_name}{extension} 已下載")
                    print(f"[INFO] 圖片路徑: {img_save_path}")
                    '''
                    image = None
                    try:
                        time.sleep(2)
                        im = Image.load(img_save_path)
                        im.verify() 
                        im.close()
                        im = Image.load(img_save_path) 
                        im.transpose(PIL.Image.FLIP_LEFT_RIGHT)
                        im.close()
                    except Exception:
                        print(f"[INFO] 偵測到圖片損毀，移除圖片: {image}")
                        os.remove(img_save_path)
                        continue
                    else:
                        print("[INFO] 圖片成功下載！")
                        
                    finally: 
                        time.sleep(2)
                    '''
                    image_count += 1
                    time_count += 1
                    
                    if time_count % 10 == 0:
                        time.sleep(2)
                        time_count = 0
            
            print("資料集當前批次(50張圖/批)圖片下載完畢！")
            
        print(f"資料集之所有圖片下載完畢！\n預期圖片下載數量: {estimated_result_num}")
        print(f"共下載 {image_count} 張，{estimated_result_num - image_count} 張無法下載")

def clothing_image_search():
    # 設定命令列參數
    ap = argparse.ArgumentParser()
    ap.add_argument("-q", "--query", required=True,
        help="response query to response Bing Image API for")
    ap.add_argument("-o", "--output", required=False,
        help="path to output directory of images")
    ap.add_argument("-i", "--index", required=True,
        help="index to identify which 'color_category' to download images")
    
    args = vars(ap.parse_args())
    
    # 設定 Bing Search v7 API 的 API 呼叫資訊 (API key & endpoint API URL)
    API_KEY = "be5ebf6cee0e41c4a818c5982c8aec27"
    #"09f968b4c3a8468782bcd68cd7383bc9" //free
    # a39a10aa41c84dcc8732e342c66ae8f5  // cost
    # be5ebf6cee0e41c4a818c5982c8aec27  // fr

    SEARCH_URL = "https://api.bing.microsoft.com/v7.0/images/search"
    MAX_RESULTS = 250  # 資料筆數上限
    BATCH_SIZE = 50  # 每批次發送請求的資料筆數
    EXCEPTIONS = set([IOError, FileNotFoundError,
        exceptions.RequestException, exceptions.HTTPError,
        exceptions.ConnectionError, exceptions.Timeout])
    TOTAL_DATASET_AMOUNT = 144
    
    headers = {"Ocp-Apim-Subscription-Key" : API_KEY}
    is_failed = False
    is_idx_specified = False
    
    color_cat_idx = args["index"]
    if (color_cat_idx != "") and (color_cat_idx is not None) and (color_cat_idx.isdigit()):
        if int(color_cat_idx) in range(TOTAL_DATASET_AMOUNT):
            color_cat_idx = int(color_cat_idx)
            is_idx_specified = True
            search_term = args["query"]
        else:
            print(f"[WARNING] 指定下載的 index 超出範圍(0-{TOTAL_DATASET_AMOUNT})！")
            is_failed = True
    else:
        print("[WARNING] --index(-i) 命令列參數輸入錯誤！")
    
    dir_name = ""
    with open("./local_data/color_category_combination.txt", "r", encoding="utf-8") as fp:
        dir_name = fp.readlines()[color_cat_idx].strip()
    
    if dir_name == "":
        print("[WARNING] 錯誤！ dir_name 為空，無法讀取記錄檔以取出 dataset 名稱。")
        print("          請檢查程式 170 行附近")
        is_failed = True
    else:
        tmp_path_1 = Path("./dataset")
        tmp_path_2 = Path(dir_name)
        color_cat_path = tmp_path_1 / tmp_path_2
        
        if not Path.exists(tmp_path_1):
            Path.mkdir(tmp_path_1)
            
        if not Path.exists(color_cat_path):
            Path.mkdir(color_cat_path)
    
    if not is_failed:
        _call_BingAPI_to_image_search(search_term, BATCH_SIZE, 
                                      SEARCH_URL, headers,
                                      MAX_RESULTS, args, 
                                      EXCEPTIONS, color_cat_path,
                                      is_idx_specified,
                                      color_cat_idx)

if __name__ == "__main__":
    clothing_image_search()