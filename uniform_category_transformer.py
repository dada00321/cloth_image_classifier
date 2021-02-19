import pandas as pd
import os

def transform_big_categories_to_uniform(is_show=True):
    '''
    Returns
    -------
    similar_categories : <dict> 
                         key: big-category for classification
                         value: big-category(defined by supplier) defined by administrator,
                                as the subordinate under the key (not very crucial for classification)
    
    is_show=True: 印出流程 is_show=True: 不印出流程
    
    This func would use other funcs: 
        1) _generate_paths
        2) _get_raw_categories,
        3) _get_splitted_categories, 
        4) _get_unclassified_categories,
        5) _print_unclassified_categories
    
    By adjusting list: 'manual_def_categories' and dict: 'manual_def_dict' humanly,
    it can finally make up the dict: 'similar_categories',
    which contains the useful categories for classification as the key,
    and some useless categories as the value.
    '''
    # key: 自訂統一 big category 詞彙 value: 各家供應商 big category 詞彙 
    
    raw_categories = _get_raw_categories()
    splitted_set = _get_splitted_categories(raw_categories)
    
    # Cleasing the whole big-categories to a dict which key of the dict is A ARBITRARY CATEGORY in a cluster of similar categories    
    # 註: manual_def_categories 中分類的取名後方不加"類"(執行後結果會自動加上後字"類")，否則會有冗餘分類
    
    
    manual_def_categories = ["上衣","襯衫","內衣","外套",
						 "下身","配件","洋裝","運動",
						 "鞋","童裝","嬰幼兒","孕婦"]
    
    manual_def_dict = {"上衣":{"毛衣","大衣","針織衫"},
    				   "內衣":{"內著","家居","家居服",
    						  "家居類","内衣"},
    				   "外套":{"外套類","外套夾克","外套"},
    				   "配件":{"皮夾","絲巾","圍巾",
    						  "皮帶","帽子","飾品",
    						  "包包","其他"},
    				   "下身":{"連身褲","裙子"},
    				   "童裝":{"kids_boy","kids_girl"},
    				   "嬰幼兒":{"baby_girl","baby_boy"}}
    '''
    
    # 測試
    manual_def_categories = ["上衣","襯衫","內衣","外套",
                             "嬰幼兒","孕婦","配件"]
    manual_def_dict = {"上衣":{"毛衣","大衣","針織衫"},
    				   "內衣":{"內著","家居","家居服",
    						  "家居類","内衣"},
                       "嬰幼兒":{"baby_boy","baby_girl"},
                       "配件":{"絲巾","包包","皮夾"}}
    '''
    
    #tmp_cats = [cat.replace("類","") for cat in manual_def_categories]
    # (1) 先利用 manual_def_categories 設計出階層式的 similar_categories 雛形
    similar_categories = {f"{key}類": set([cat for raw_cat in raw_categories for cat in raw_cat.split("/") if cat in key or key in cat]) for key in manual_def_categories}
    if is_show:
        print("==="*12, "\n", "1. similar_categories 設計雛形 (依照手工添加的 manual_def_categories 所設計)", "==="*12)
        print("similar_categories:\n", similar_categories, "\n", sep='')
    
    # 印出查看目前尚未歸類的粗分類
    unclassified_cats = _get_unclassified_categories(splitted_set, similar_categories)
    if is_show:
        _print_unclassified_categories(splitted_set, similar_categories, unclassified_cats)
    
    # (2) 再透過 manual_def_dict 補償修正:「??廠商分類 應分在 ??自訂分類下(作為子分類)」
    if is_show:
        print("==="*12, "\n", "2. 歸類補償修正後 (依照手工添加的 manual_def_dict) 補償修正", "==="*12, sep='')
    #for manual_main_cat, manual_sub_cat in manual_def_dict.items():
    for unclassified_cat in unclassified_cats:
        #print(f"\"{unclassified_cat}\"", end=" ")
        for manual_main_cat, manual_sub_cats in manual_def_dict.items():
            for manual_sub_cat in manual_sub_cats:
                #print(manual_sub_cat)
                if unclassified_cat in manual_sub_cat:
                    #similar_categories[manual_main_cat].add(manual_sub_cat)
                    similar_categories[f"{manual_main_cat}類"].add(manual_sub_cat)
    if is_show:
        print("similar_categories:\n", similar_categories, "\n", sep='')
    
    '''tmp_cats = [cat.replace("類","") for cat in manual_def_categories]
    for raw_cat in raw_categories:
        if raw_cat in tmp_cats:
    print(similar_categories,"\n\n")
    '''
    # 印出查看目前尚未歸類的粗分類
    unclassified_cats = _get_unclassified_categories(splitted_set, similar_categories)
    if is_show:
        _print_unclassified_categories(splitted_set, similar_categories, unclassified_cats)
    
    # 若確定 similar_categories 正確，回傳 similar_categories
    return similar_categories

def _generate_paths():
    # Generate clear path of CSV files for all cloth suppliers
    base_path_1 = "./local_data/Lativ_Crawler/res/tier_1.csv"
    base_path_2 = "./local_data/Other_Supplier_Crawlers/output/tier1/csv/"
    csv_file_names = os.listdir(base_path_2)
    csv_paths = [base_path_1] + [base_path_2+csv_fn for csv_fn in csv_file_names if "H&M" not in csv_fn]
    #print(*(f"({i+1}) {path}" for i, path in enumerate(csv_paths)), len(csv_paths), "\n", sep="\n")
    return csv_paths

def _get_raw_categories():
    # Read all big-categories and put them to 'tmp_list'
    raw_categories = set(category for csv_path in _generate_paths() for category in pd.read_csv(csv_path)["category"])
    #print(raw_categories, len(raw_categories), "\n") # 48=>39( list => set ), 9 duplicated categorie names
    return raw_categories

def _get_splitted_categories(raw_categories):
    # Splitting some compound categories (which combines many types) into single-term categories
    spliter = "/"
    splitted_set = set()
    for cat in raw_categories:
        cat = cat.replace("・","/").replace("&","/")
        if spliter in cat:
            #print(cat.replace("&","/").split("/"))
            [splitted_set.add(cat) for cat in cat.split("/")]
        else:
            splitted_set.add(cat)
    #print(splitted_set, len(splitted_set), "\n") # 39=>43, 4 additional categories appended after splitting categories which combines many types
    return splitted_set

def _get_unclassified_categories(splitted_set, similar_categories):
    # 回傳當前尚未歸類(進 similar_categories)的粗分類到 existing_cats
    unclassified_cats = splitted_set - set(cat for v in similar_categories.values() for cat in v)
    return unclassified_cats

def _print_unclassified_categories(splitted_set, similar_categories, unclassified_cats):
    #print("existing_cats:\n", existing_cats, "\n", sep='')
    
    # 印出查看目前尚未歸類的粗分類
    # 手動確認要增設哪些分類後，可增加自訂新分類到 manual_def_categories
    # 或是增加自訂新從屬階層到 manual_def_dict
    print("執行本階段後，尚未歸類的粗分類:")
    if len(unclassified_cats) > 0:
        print(*(f"\'{cat}\'" for cat in unclassified_cats), "\n", sep="/")
    else:
        print("無")
#-----------------------------
def get_main_categories(is_show=True):
    '''
    Returns
    -------
    list(similar_categories.keys()): <list>
    
    This func only use 1 other func: 'transform_big_categories_to_uniform'
    to obtain uniform, upper-level categories,
    as the role of FEATURES to help to train classification model.
    '''
    similar_categories = transform_big_categories_to_uniform(is_show)
    #print(similar_categories)
    return list(similar_categories.keys())

def list_all_combination(is_show=False):
    clothing_color_path = "./local_data/color_sheet.txt"
    colors = list()
    with open(clothing_color_path, "r") as fp:
        [colors.append(color) for line in fp.readlines()[1:] for color in line.rstrip().split("：")[-1].split("、")]
    #print(colors)
    
    main_categories = get_main_categories(is_show=False)
    #print(main_categories)
    
    # 12 categories x 12 colors => 144 sets 
    train_feature_combination = [f"{color}色_{cat}" for color in colors for cat in main_categories]
    #print(train_feature_combination)
    
    if is_show:
        for i, color_cat in enumerate(train_feature_combination):
            print(f"{str(i).zfill(6)}_{color_cat}")
    return train_feature_combination
    
def write_all_combination_to_txt():
    train_feature_combination = list_all_combination(is_show=False)
    color_cat_combination_path = "./local_data/color_category_combination.txt"
    try:
        with open(color_cat_combination_path, "w") as fp:
            tmp = len(train_feature_combination)-1
            for i, color_cat in enumerate(train_feature_combination):
                #print(f"{str(i).zfill(6)}_{color_cat}")
                msg = f"{str(i).zfill(6)}_{color_cat}"
                msg += "\n" if i != tmp else ""
                fp.write(msg)
                
    except Exception as e:
        print(f"'顏色_服飾分類'txt檔: {color_cat_combination_path} 寫入失敗:")
        print(str(e))
    else:
        print(f"'顏色_服飾分類'txt檔: {color_cat_combination_path} 寫入成功！")
        
if __name__ == "__main__":
    ''' 功能 1: 歸納整理各服飾供應商服飾(粗)分類 '''
    '''
    main_categories = get_main_categories(is_show=True) #顯示過程
    #main_categories = get_main_categories(is_show=False) #不顯示過程
    print("\n", "==="*12, "\n", "用來訓練所有的上層分類", "==="*12, "\n", main_categories, len(main_categories), sep='')
    '''
    
    ''' 功能 2: 列出所有:'顏色_服飾分類'的排列組合，作為查詢關鍵字的輸入
               (E.g., Azure-API 呼叫 => 到 Bing 搜尋 => 送 request 存圖)'''
    
    #list_all_combination(is_show=True)
    
    ''' 功能 3: 儲存所有:'顏色_服飾分類'的排列組合 (不含紀錄) 為 txt檔 '''
    #write_all_combination_to_txt()
    
