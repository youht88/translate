import logging
from ylz_translate.utils.crypto_utils import HashLib
from ylz_translate.utils.data_utils import Color
from ylz_translate.utils.file_utils import FileLib
from ylz_translate.utils.soup_utils import SoupLib

def syncDict(args):
        dictionary = FileLib.loadJson("dictionary.json")
        mode = args.mode
        if mode == "json":
            mode_fix = "json"
        elif mode == "html":
            mode_fix = "html"
        else:
            mode_fix = "md"
        dict_hash = args.dict_hash    
        url_id = args.url_id
        url = args.url
        url_file = args.url_file
        url_ids = []
        only_list  = args.only_list
        
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
            error = False
            for url_id in url_ids:
                if error:
                    logging.info("="*50)
                error = False
                #setp 1
                miss_hashs = _check_valueHash_in_dict(url_id,mode,dictionary)
                if len(miss_hashs)>0:
                    error = True
                    logging.info(f"{Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{str(miss_hashs)}{Color.RESET}在字典中没有找到,请同步!")
                #setp 2 
                miss_block_refs = _check_block_in_ref(url_id,mode,dictionary)
                if len(miss_block_refs)>0:
                    error = True
                    for miss_block_ref in miss_block_refs:
                        logging.info(f"{Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{miss_block_ref['block_idx']}--{miss_block_ref['value_hash']}{Color.RESET}在字典ref中没有找到,请同步!")           
                #setp 3
                miss_ref_blocks = _check_ref_in_block(url_id,mode,dictionary)
                if len(miss_ref_blocks)>0:
                    error = True
                    for miss_ref_block in miss_ref_blocks:
                        logging.info(f"{Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{miss_ref_block['block_idx']}--{miss_ref_block['value_hash']}{Color.RESET}在block中没有找到,请同步!")           
        except Exception as e:
            logging.info("同步字典失败!"+str(e)) 

def _check_valueHash_in_dict(url_id,mode,dictionary) -> list[str]:
     # step1 查看url_id的所有dict_hash是否都在dictionary，如果不在指出缺失项
    miss_hashs=[]
    value_dict = FileLib.loadJson(f"temp/{url_id}/{mode}/value_dict.json")
    for value_hash in value_dict:
        if value_hash not in dictionary:
            miss_hashs.append(value_hash)
    return miss_hashs
    
def _check_block_in_ref(url_id,mode,dictionary) -> list[str]:
    file_contents = FileLib.readFiles(f"temp/{url_id}/{mode}","part_[0-9]*_en.html")
    blocks = [ item[1] for item in sorted(file_contents.items())]     
    miss_block_refs = []
    for block_idx ,block in enumerate(blocks):
        soup_block = SoupLib.html2soup(block)
        items = soup_block.find_all(lambda tag:tag.get("path") and tag.get("value"))
        for block_item  in items:
            value_hash = block_item.get("value")
            dict_item = dictionary.get(value_hash,{})
            dict_item_refs = dict_item.get(f"{mode}_refs",[])
            finded = False
            for ref in dict_item_refs:
                ref_url_id = ref.get("url_id")
                ref_block_idx = ref.get("block_idx")
                if ref_url_id == url_id and ref_block_idx == block_idx:
                    finded = True
                    break
            if not finded:
                miss_block_refs.append({"block_idx":block_idx,"value_hash":value_hash}) 
    return miss_block_refs
def _check_ref_in_block(url_id,mode,dictionary) -> list[str]:
    miss_ref_blocks = []
    for dict_hash in dictionary:
        dict_item = dictionary.get(dict_hash,{})
        refs = dict_item.get(f"{mode}_refs",[])
        for ref in refs:
            ref_url_id = ref.get("url_id")
            ref_block_idx = ref.get("block_idx")
            if ref_url_id == url_id:
                file_content = FileLib.readFile(f"temp/{url_id}/{mode}/part_{str(ref_block_idx).zfill(3)}_en.html")
                soup_block = SoupLib.html2soup(file_content)
                items = soup_block.find_all(lambda tag:tag.get("path") and tag.get("value"))
                finded = False
                for block_item  in items:
                    value_hash = block_item.get("value")
                    if value_hash == dict_hash:
                        finded = True
                        break
                if not finded:
                    miss_ref_blocks.append({"block_idx":ref_block_idx,"value_hash":value_hash}) 
    return miss_ref_blocks
'''
                #删除对应的temp目录或对应cn文件
                if len(block_idxs)==0:
                    FileLib.rmdir(f"temp/{url_id}/{mode}")
                else:
                    for block_idx in block_idxs:
                        FileLib.rmFile(f"temp/{url_id}/{mode}/part_{str(block_idx).zfill(3)}_cn.html")   
                #删除dictionary对应的refs
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
                    
            #FileLib.dumpJson("dictionary.json",dictionary) 
'''        
