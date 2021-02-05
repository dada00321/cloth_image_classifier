# USAGE
# python clothing_image_searcher.py --index n
# (index: n in range of [0, 143])

from requests import exceptions
import argparse
import requests
from PIL import Image
import PIL
#import cv2
import os
from pathlib import Path
import time

def _insert_successful_log_message(color_cat_idx):
    train_feature_combination = _read_all_combination()
    #print(*(line for line in train_feature_combination), sep="\n")
    
    if train_feature_combination is not None and color_cat_idx is not None:
        color_cat_combination_path = "./local_data/color_category_combination.txt"
        msg = "正在寫入 dataset 狀態記錄檔\n"
        msg += "請輸入y以繼續 [y/n]:"
        while True:
            ans = input(msg)
            if ans.lower() == "y": break

        log_msg = ""
        leng = len(train_feature_combination)
        for i in range(leng):
            log_msg += train_feature_combination[i]
            if i == color_cat_idx:
                log_msg += "_is_completed"
            if i != (leng-1):
                log_msg += "\n"

        try:
            with open(color_cat_combination_path, "w") as fp:
                fp.write(log_msg)
        except Exception as e:
            print(f"dataset 狀態記錄檔: {color_cat_combination_path} 寫入失敗:")
            print(str(e))
        else:
            print("dataset 狀態記錄檔 寫入成功！")
            print(f"請至路徑: {color_cat_combination_path} 查看")
        
def _read_all_combination():
    color_cat_combination_path = "./local_data/color_category_combination.txt"
    train_feature_combination = None
    try:
        with open(color_cat_combination_path, "r") as fp:
            train_feature_combination = [line.strip() for line in fp.readlines()]
        #print(train_feature_combination, len(train_feature_combination))
    except Exception:
        print("[INFO] dataset 狀態記錄檔讀取失敗，請檢查檔案是否遺失")
        print("[TIPS] 若確定遺失，可至 uniform_category_transformer.py 重新寫入一份 dataset 狀態記錄檔")
    finally:
        if train_feature_combination is not None:
            return train_feature_combination
        return None
    
def _create_categorized_dir(combination_or_dirname, color_cat_idx=-1):
    tmp_path = Path("./dataset")
    if not tmp_path.exists(): 
        tmp_path.mkdir()
    
    if color_cat_idx != -1: # (color_cat) combination
        dir_name = combination_or_dirname[color_cat_idx] 
        tmp_path = Path("./dataset") / Path(dir_name)
    else: # dirname
        tmp_path = Path("./dataset") / Path(combination_or_dirname)
    
    if not tmp_path.exists(): 
        tmp_path.mkdir()
    return tmp_path
    
def _call_BingAPI_to_image_search(search_term, BATCH_SIZE, 
                                  SEARCH_URL, headers,
                                  MAX_RESULTS, args, 
                                  EXCEPTIONS, img_save_dir,
                                  is_idx_specified,
                                  color_cat_idx=None):
    
    if is_idx_specified:
        # 下為預設:
        #search_term = f'{search_term.split(" ")[0]} {search_term.split(" ")[1][:-1]} 服飾'
        
        # 下為自訂:
        #search_term = "Maternity clothes gray"
        search_term = "black bag"

        # 紅色太偏橙色可保留，放到另一個資料夾(或直接刪除/省時)
        # 目標: 每個分類夾有 350~400 張圖
        # 為做比較好的顏色區隔(與相近顏色，只取明顯是該顏色的data)
        # 有多張人像、背景太複雜的，可直接刪除，或手工去背、截圖
        #search_term = "red jacket clothing"
        # 為搜尋出更合適的資料，不用預設的文字，自訂搜尋詞
        # P.S. 搜尋法文、英文、日文、韓文等會有該國流行服飾，比用繁中找的更多
    
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
    image_count = 0
    time_count = 0
    
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
            print(f"圖片副檔名: {extension}")
            
            try:
                r = requests.get(img_link, timeout=30)
                img_file_name = str(image_count+583).zfill(8)
                img_save_path = Path(img_save_dir) / Path(img_file_name + extension)
                with open(img_save_path, "wb") as fp:
                    fp.write(r.content)
                
            except Exception as e:
                if e in EXCEPTIONS:
                    print(f"[INFO] 無法下載圖片: {img_link}")
                    continue
                else:
                    print("[INFO] 未知的錯誤:\n" + str(e))
                    continue
            
            else: # 若圖片下載成功
                print(f"圖片{img_file_name}{extension} 已下載")
                print(f"圖片路徑: {img_save_path}")
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
    # 若為指定參數 --index(-i) 的命令，則 insert 一筆表示成功的 log file
    if is_idx_specified:
        _insert_successful_log_message(color_cat_idx)
    
def clothing_image_search():
    # 設定命令列參數
    ap = argparse.ArgumentParser()
    ap.add_argument("-q", "--query", required=False,
        help="response query to response Bing Image API for")
    ap.add_argument("-o", "--output", required=False,
        help="path to output directory of images")
    ap.add_argument("-i", "--index", required=True,
        help="index to identify which 'color_category' to download images")
    
    args = vars(ap.parse_args())
    
    # 設定 Bing Search v7 API 的 API 呼叫資訊 (API key & endpoint API URL)
    API_KEY = "09f968b4c3a8468782bcd68cd7383bc9"
    SEARCH_URL = "https://api.bing.microsoft.com/v7.0/images/search"
    MAX_RESULTS = 250  # 資料筆數上限
    BATCH_SIZE = 50  # 每批次發送請求的資料筆數
    EXCEPTIONS = set([IOError, FileNotFoundError,
        exceptions.RequestException, exceptions.HTTPError,
        exceptions.ConnectionError, exceptions.Timeout])
    
    headers = {"Ocp-Apim-Subscription-Key" : API_KEY}
    is_failed = False
    is_idx_specified = False
    
    color_cat_idx = args["index"]
    train_feature_combination = _read_all_combination()
    if (color_cat_idx != "") and (color_cat_idx is not None) and (color_cat_idx.isdigit()):
        if int(color_cat_idx) in range(0, len(train_feature_combination)):
            color_cat_idx = int(color_cat_idx)
            color_cat_path = _create_categorized_dir(train_feature_combination, color_cat_idx)
            is_idx_specified = True
            tmp = train_feature_combination[color_cat_idx]
            search_term = tmp.split("_")[1] + " " + tmp.split("_")[2]
        else:
            print(f"[INFO] 指定下載的 index 超出範圍(0-{len(train_feature_combination)})！")
            is_failed = True
    
    else:
        search_term = args["query"]
        if search_term.strip() != "" or search_term is not None:
            color_cat_path = _create_categorized_dir(search_term)
        else:
            print("[INFO] 指定下載的資料夾名稱錯誤！")
            is_failed = True
    
    img_save_dir = args["output"]
    if img_save_dir == "" or img_save_dir is None:
        img_save_dir = color_cat_path
    
    img_save_dir = color_cat_path
    
    if not is_failed:
        _call_BingAPI_to_image_search(search_term, BATCH_SIZE, 
                                      SEARCH_URL, headers,
                                      MAX_RESULTS, args, 
                                      EXCEPTIONS, img_save_dir,
                                      is_idx_specified,
                                      color_cat_idx)

if __name__ == "__main__":
    clothing_image_search()