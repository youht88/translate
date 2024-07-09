import logging
import re

from ylz_translate.utils.file_utils import FileLib
from ylz_translate.utils.crypto_utils import HashLib
from ylz_translate.utils.soup_utils import SoupLib
from ylz_translate.utils.data_utils import Color

def _replaceSoupText(pattern,soup,replace_text=None) -> bool:
    string_elements = soup.find_all(string=True)
    isMatch = False
    sample_text = ""
    for element in string_elements:
        searched = re.search(pattern,str(element.string))
        if searched:
            isMatch = True
            matched_group0 = searched.group(0)
            #print(type(element),type(element.parent),str(element.parent),matched.string,matched.groups())
            new_matched_group0=None
            if len(searched.groups())>0:
                matched_group1 = searched.group(1)
                if replace_text!=None:
                    new_matched_group0 = matched_group0.replace(matched_group1, replace_text, 1) 
            else:
                matched_group1 = matched_group0
                if replace_text!=None:
                    new_matched_group0 = replace_text
            temp1 = str(element.parent).replace(matched_group0,"__@@@@__")
            temp2 = _markText(matched_group0,pattern,visble_len=100)
            sample_text = temp1.replace("__@@@@__",temp2)
            #### 更新
            if replace_text!=None:
                if len(searched.groups())>0:
                    new_matched_group0 = matched_group0.replace(matched_group1, replace_text, 1) 
                else:
                    new_matched_group0 = replace_text
                #print("===>",str(element).replace(matched_group0,new_matched_group0))
                element.replace_with(str(element).replace(matched_group0,new_matched_group0))
            # print("===="*10)
            # print(SoupLib.soup2html(soup))
            # print("====="*10)
            break
    return isMatch,SoupLib.soup2html(soup),sample_text
    
def _markText(old_text,text_repl,visble_len=100) -> str:
    # text是old_text的文本
    # 在old_text上以【】标注text，并前后visble_len个字符，其他以省略号替代，返回这个标注的文本
    search = re.search(text_repl,old_text)
    if not search:
        return old_text
    reg = search.regs[-1]    
    text = search.string[reg[0]:reg[1]]
    left = reg[0]
    right = reg[1]
    left_begin = left - visble_len if left > visble_len else 0
    left_dots = "..." if left_begin > 0 else ""
    right_end = right + visble_len if right + visble_len < len(old_text) else len(old_text)
    right_dots = "..." if right_end < len(old_text) else ""
    markedText = f"{left_dots}{old_text[left_begin:left]}【{text}】{old_text[right:right_end]}{right_dots}"
    return markedText

def fixDict(args):
        dictionary = FileLib.loadJson("dictionary.json")

        mode = args.mode
        if mode == "json":
            mode_fix = "json"
        elif mode == "html":
            mode_fix = "html"
        else:
            mode_fix = "md"
        
        dict_hash_init = args.dict_hash
        issubtext = args.issubtext
        arg_old_text = args.old_text
        arg_new_text = args.new_text
        only_list = args.only_list
        arg_ref_url_ids = args.url_ids if args.url_ids else []
        arg_origin_text_pattern = args.origin_text_pattern

        if (dict_hash_init==None and arg_old_text==None):
            logging.info("必须指定--dict_hash、--old_text和中至少的一个!")
            return
        if not arg_new_text:
            arg_new_text=""
            logging.info(f"{Color.LRED}--new_text为空，请检查这是否合理!!!{Color.RESET}")
        if dict_hash_init!=None and issubtext==True:
            logging.info("字典hash模式下--issubtext必须为False!")
            return
        if dict_hash_init!=None and len(dict_hash_init)!=6:
            logging.info("字典的hash值必须位6位!")
            return

        dict_hashs = []        
        for dict_hash in dictionary:
            if dict_hash_init != None and  dict_hash != dict_hash_init:
                continue
            dict_item = dictionary.get(dict_hash)
            old_target_text = dict_item.get("target_text")
            old_origin_text = dict_item.get("origin_text")
            shrinked_origin_text = old_origin_text.replace("\n","").replace("\xa0","").replace("\xa3","")
                
            if mode=="json":
                refs = dict_item.get("json_refs",[])
            elif mode=="html":
                refs = dict_item.get("html_refs",[])
            else :
                refs = dict_item.get("markdown_refs",[])
            
            ref_info = []
            for ref in refs:
                if len(arg_ref_url_ids)==0 or ref.get("url_id") in arg_ref_url_ids:
                    ref_info.append(f"{ref['url_id']}-{ref['block_idx']}")
            if ref_info:
                sample_text=""
                isMatch = False
                if arg_origin_text_pattern:
                    old_origin_soup = SoupLib.html2soup(old_origin_text)                  
                    isMatch,_,_ = _replaceSoupText(arg_origin_text_pattern,old_origin_soup)
                    if not isMatch:
                        continue 
                if not issubtext:
                    if arg_old_text!=None and  old_target_text != arg_old_text:
                        continue
                    dict_hashs.append(dict_hash)
                    idx = len(dict_hashs)
                    if only_list:            
                        logging.info(f"{Color.YELLOW}{idx}.字典hash:{dict_hash}{Color.RESET}")
                        logging.info(f"{Color.RED}ref_url_ids:{Color.RESET}{ref_info}")
                        logging.info(f"{Color.GREEN}原始文本:{Color.RESET}{shrinked_origin_text}")
                        logging.info(f"{Color.GREEN}旧目标文本:{Color.RESET}{old_target_text}")
                        logging.info(f"{Color.GREEN}新目标文本:{Color.RESET}【{arg_new_text}】\n")
                else:
                    arg_target_text_pattern = arg_old_text
                    if arg_target_text_pattern:
                        old_target_soup = SoupLib.html2soup(old_target_text)
                        isMatch,_,sample_text = _replaceSoupText(arg_target_text_pattern, old_target_soup)
                        if not isMatch:
                            continue
                    dict_hashs.append(dict_hash)
                    idx = len(dict_hashs)
                    if only_list:
                        logging.info(f"{Color.LYELLOW}{idx}.字典hash:{dict_hash}{Color.RESET}")
                        logging.info(f"{Color.LRED}ref_url_ids:{Color.RESET}{ref_info}")
                        logging.info(f"{Color.LGREEN}原始文本:{Color.RESET}{shrinked_origin_text}")
                        logging.info(f"{Color.LGREEN}旧目标文本:{Color.RESET}{sample_text}")
                        logging.info(f"{Color.LGREEN}新目标文本:{Color.RESET}...【{arg_new_text}】...\n")

        logging.info(f"找到{len(dict_hashs)}个字典hash\n{dict_hashs}")
        if only_list:
            return
        try:
            for dict_hash in dict_hashs:
                dict_item = dictionary.get(dict_hash)
                if not dict_item:
                    logging.info(f"没有找到字典hash={dict_hash}的数据!")
                    return
                old_target_text = dict_item.get("target_text")
                if not issubtext:
                    dict_item["target_text"] = arg_new_text
                else:
                    old_target_soup = SoupLib.html2soup(old_target_text)
                    isMatch, new_soup_html,_ = _replaceSoupText(arg_old_text,old_target_soup,arg_new_text)
                    if isMatch:
                        dict_item["target_text"] = new_soup_html
                #logging.info(f"将字典hash={dict_hash}的目标文字\n由【{old_target_text}】\n改为【{dict_item['target_text']}】\n原始文字为:【{shrink_origin_text}】")

                if mode=="json":
                    refs = dict_item.get("json_refs",[])
                elif mode=="html":
                    refs = dict_item.get("html_refs",[])
                else :
                    refs = dict_item.get("markdown_refs",[])
                for ref in refs:
                    ref_item_url_id = ref.get("url_id")
                    if len(arg_ref_url_ids)==0 or (ref_item_url_id in arg_ref_url_ids):
                        ref_item_block_idx = ref.get("block_idx")
                        #logging.info(f"???,dict_hash={dict_hash},ref_item_url_id={ref_item_url_id},ref_item_block_idx={ref_item_block_idx}")
                        if ref_item_url_id!=None and ref_item_block_idx!=None:
                            FileLib.rmFile(f"temp/{ref_item_url_id}/{mode}/part_{str(ref_item_block_idx).zfill(3)}_cn.html")
                            FileLib.rmFile(f"{ref_item_url_id}_cn.{mode_fix}")            
            FileLib.dumpJson("dictionary.json",dictionary)
        except Exception as e:
            logging.info("更新字典失败!"+str(e))