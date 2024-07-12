import logging
from ylz_translate.utils.crypto_utils import HashLib
from ylz_translate.utils.data_utils import Color
from ylz_translate.utils.file_utils import FileLib
from ylz_translate.utils.soup_utils import SoupLib

def syncDict(args):
        dictionary = FileLib.loadJson("dictionary.json")
        mode = args.mode
        dict_hash = args.dict_hash    
        url_id = args.url_id
        url = args.url
        url_file = args.url_file
        url_ids = []
        clear_step4  = args.clear_step4
        
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
            dict_hashs = set(dictionary.keys())
            for url_id in url_ids:
                if error:
                    logging.info("="*50)
                error = False
                #step 1.1
                miss_hashs_from_dict = _check_valueHash_from_dict(url_id,mode,dictionary)
                if len(miss_hashs_from_dict)>0:
                    error = True
                    logging.info(f"{Color.LGREEN}step1.1{Color.RESET} {Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{str(miss_hashs_from_dict)}{Color.RESET}在字典中没有找到,请同步!")
                #step 1.2
                miss_enblocks_inter_cnblocks = _check_enblocks_inter_cnblocks(url_id,mode,dictionary)
                if len(miss_enblocks_inter_cnblocks)>0:
                    error = True
                    for miss_hash in miss_enblocks_inter_cnblocks:
                        logging.info(f"{Color.LGREEN}step1.2{Color.RESET} {Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{miss_hash['block_idx']}--{str(miss_hash['value_hashs'])}{Color.RESET}在en block中存在而在cn block丢失,请同步!")
                #step 2 
                miss_block_refs = _check_block_in_ref(url_id,mode,dictionary)
                if len(miss_block_refs)>0:
                    error = True
                    for miss_block_ref in miss_block_refs:
                        logging.info(f"{Color.LGREEN}step2{Color.RESET} {Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{miss_block_ref['block_idx']}--{miss_block_ref['value_hash']}{Color.RESET}在字典ref中没有找到,请同步!")           
                #step 3
                miss_ref_blocks = _check_ref_in_block(url_id,mode,dictionary)
                if len(miss_ref_blocks)>0:
                    error = True
                    for miss_ref_block in miss_ref_blocks:
                        logging.info(f"{Color.LGREEN}step3{Color.RESET} {Color.LRED}{url_id}{Color.RESET}的{mode}模式下{Color.LYELLOW}{miss_ref_block['block_idx']}--{miss_ref_block['value_hash']}{Color.RESET}在block中没有找到,请同步!")           
                #step 4
                value_dict = FileLib.loadJson(f"temp/{url_id}/{mode}/value_dict.json")
                dict_hashs = dict_hashs -  set(value_dict.keys())          
            if len(dict_hashs)>0:       
                error = True
                logging.info(f"{Color.LGREEN}step4{Color.RESET} {mode}模式下{Color.LYELLOW}字典中的{str(dict_hashs)}{Color.RESET}在所有blocks中没有找到,请同步!")
                if clear_step4:
                    FileLib.dumpJson("dictionary.json.bak",dictionary)
                    for dict_hash in dict_hashs:
                        dictionary.pop(dict_hash)
                    FileLib.dumpJson("dictionary.json",dictionary)
        except Exception as e:
            logging.info("同步字典失败!"+str(e)) 

def _check_valueHash_from_dict(url_id,mode,dictionary) -> list[str]:
     # step1.1 查看url_id的所有dict_hash是否都在dictionary，如果不在指出缺失项
    miss_hashs=[]
    value_dict = FileLib.loadJson(f"temp/{url_id}/{mode}/value_dict.json")
    for value_hash in value_dict:
        if value_hash not in dictionary:
            miss_hashs.append(value_hash)
    return miss_hashs
def _check_enblocks_inter_cnblocks(url_id,mode,dictionary) -> list[str]:
     # step1.2 查看url_id的所有en blocks的hash是否都在对应的cn blocks中，如果不在指出缺失项
    miss_hashs=[]
    file_cn_contents = FileLib.readFiles(f"temp/{url_id}/{mode}","part_[0-9]*_cn.html")
    cn_blocks = [ item[1] for item in sorted(file_cn_contents.items())]    
    file_en_contents = FileLib.readFiles(f"temp/{url_id}/{mode}","part_[0-9]*_en.html")
    en_blocks = [ item[1] for item in sorted(file_en_contents.items())]    
    if len(en_blocks) != len(cn_blocks):
        logging.info(f"{Color.LGREEN}step1.2{Color.RESET} {Color.LRED}{url_id}{Color.RESET}的blocks不完整,请重新生成")
        return []
    for block_idx ,en_block in enumerate(en_blocks):
        en_soup_block = SoupLib.html2soup(en_block)
        en_items = en_soup_block.find_all(lambda tag:tag.get("path") and tag.get("value"))
        en_block_hashs = set([block_item.get("value") for block_item in en_items])
        cn_soup_block = SoupLib.html2soup(cn_blocks[block_idx])
        cn_items = cn_soup_block.find_all(lambda tag:tag.get("path") and tag.get("value"))
        cn_block_hashs = set([block_item.get("value") for block_item in cn_items])
        miss_block_hashs = en_block_hashs - cn_block_hashs
        if len(miss_block_hashs)>0:
            miss_hashs.append({"block_idx":block_idx,"value_hashs":miss_block_hashs})
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
                    miss_ref_blocks.append({"block_idx":ref_block_idx,"value_hash":dict_hash}) 
    return miss_ref_blocks
