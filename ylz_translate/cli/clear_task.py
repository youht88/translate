import logging
from ylz_translate.utils.crypto_utils import HashLib
from ylz_translate.utils.data_utils import Color
from ylz_translate.utils.file_utils import FileLib

def clearTask(args):
        dictionary = FileLib.loadJson("dictionary.json")
        mode = args.mode
        if mode == "json":
            mode_fix = "json"
        elif mode == "html":
            mode_fix = "html"
        else:
            mode_fix = "md"
    
        url_id = args.url_id
        url = args.url
        url_file = args.url_file
        url_ids = []
        block_idxs = args.blocks if args.blocks else []
        only_final = args.only_final
        deep_clear = args.deep_clear
        if not url and not url_id and not url_file:
            logging.info("必须指定url_id或者url,或者url_file!")
            return
        if url_id!=None:
            url_ids = [url_id]
        elif url:
            url_id = HashLib.md5(url)
            url_ids = [url_id]
        else:
            file_text = FileLib.readFile(url_file)
            urls = file_text.split("\n")
            url_ids = [HashLib.md5(url) for url in urls]    
        try:
            for url_id in url_ids:
                FileLib.rmFile(f"{url_id}_cn.{mode_fix}")
            if only_final:
                return
            for url_id in url_ids:
                #删除对应的temp目录或对应cn文件
                if len(block_idxs)==0:
                    FileLib.rmdir(f"temp/{url_id}/{mode}")
                else:
                    for block_idx in block_idxs:
                        FileLib.rmFile(f"temp/{url_id}/{mode}/part_{str(block_idx).zfill(3)}_cn.html")   
                #删除dictionary对应的refs
                dict_pop_hash = []
                for dict_hash in dictionary:
                    dict_item = dictionary.get(dict_hash,{})
                    if mode=="json":
                        refs = dict_item.get("json_refs",[])
                    elif mode=="html":
                        refs = dict_item.get("html_refs",[])
                    else :
                        refs = dict_item.get("markdown_refs",[])
                    new_refs = []
                    for ref in refs:
                        ref_item_url_id = ref.get("url_id")
                        ref_item_block_idx = ref.get("block_idx")
                        if ref_item_url_id != url_id:
                            new_refs.append(ref)
                        else:
                            if len(block_idxs)!=0 and (ref_item_block_idx not in block_idxs):
                                new_refs.append(ref)
                    refs = new_refs.copy()
                    if mode=="json":
                        dict_item["json_refs"] = refs
                    elif mode=="html":
                        dict_item["html_refs"] = refs
                    else :
                        dict_item["markdown_refs"] = refs
                    
                    if deep_clear:
                        if len(refs)==0:
                            dict_pop_hash.append(dict_hash)
                    
                if deep_clear:
                    logging.info(f"将删除以下字典的以下hash:{Color.LYELLOW}{str(dict_pop_hash)}{Color.RESET}")
                    for dic_hash in dict_pop_hash:
                        dictionary.pop(dic_hash)
                    
            FileLib.dumpJson("dictionary.json",dictionary) 
        except Exception as e:
            logging.info("清除任务失败!"+str(e)) 
