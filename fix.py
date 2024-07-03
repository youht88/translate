
import logging
import os
import sys
import argparse

from translate.utils.file_utils import FileLib
from translate.utils.crypto_utils import HashLib

def main():
    parser = argparse.ArgumentParser(description = "维护工具")
    parser.add_argument("--mode", required=True, choices=["markdown","html","json"],help="处理模式(markdown|html|json)")
    
    subparsers = parser.add_subparsers(dest="command", help="使用子命令")

    fixDict_parser = subparsers.add_parser("fixdict", help="更新字典")
    fixDict_parser.add_argument("--dict_hash", required=True, help="字典的hash值(6位)")
    fixDict_parser.add_argument("--text",required=True,help="字典的hash所对应的目标文字")

    syncDict_parser = subparsers.add_parser("syncdict", help="同步字典")
    syncDict_parser.add_argument("--dict_hash", required=True, help="字典的hash值(6位)")
    
    clearTask_parser = subparsers.add_parser("cleartask", help="清除已完成的url翻译,以便重新翻译")
    clearTask_parser.add_argument("--url_hash",help="任务的url hash值(32位)")
    clearTask_parser.add_argument("--url", help="任务的url,如果同时指定了--ulr_hash则忽略此参数")
    clearTask_parser.add_argument("-f","--url_file",type=str,help="包含一行或多行url的文件,指定--url或--url_hash时忽略此参数")
    clearTask_parser.add_argument("--block",nargs="*",type=int,help="要删除的block index列表")
    clearTask_parser.add_argument("--only_final", default = False,help="仅删除最终的结果文件")
    
    args = parser.parse_args()
    logging.info(str(args))

    task = FileLib.loadJson("task.json")
    dictionary = FileLib.loadJson("dictionary.json")

    mode = args.mode
    if mode == "json":
        mode_fix = "json"
    elif mode == "html":
        mode_fix = "html"
    else:
        mode_fix = "md"
    
    if args.command == "fixdict":    
        dict_hash = args.dict_hash
        dict_target_text = args.text
        if len(dict_hash)!=6:
            logging.info("字典的hash值必须位6位!")
            return
        if len(dict_target_text)==0:
            logging.info("字典的hash所对应的目标文字不能位空!")
            return
                
        try:
            dict_item = dictionary.get(dict_hash)
            if not dict_item:
                logging.info(f"没有找到字典hash={dict_hash}的数据!")
                return
            origin_text = dict_item.get("origin_text")
            old_target_text = dict_item.get("target_text")
            dict_item["target_text"] = dict_target_text
            logging.info(f"将字典hash={dict_hash}的目标文字\n由【{old_target_text}】\n改为【{dict_target_text}】\n原始文字为:【{origin_text}】")
            if mode=="json":
                refs = dict_item.get("json_refs",[])
            elif mode=="html":
                refs = dict_item.get("html_refs",[])
            else :
                refs = dict_item.get("markdown_refs",[])
            for ref in refs:
                ref_item_url_id = ref.get("url_id")
                ref_item_block_idx = ref.get("block_idx")
                if ref_item_url_id and ref_item_block_idx:
                    FileLib.rmFile(f"temp/{ref_item_url_id}/{mode}/part_{str(ref_item_block_idx).zfill(3)}_cn.html")
                    FileLib.rmFile(f"{ref_item_url_id}_cn.{mode_fix}")            
            FileLib.dumpJson("dictionary.json",dictionary)
        except Exception as e:
            logging.info("更新字典失败!"+str(e))
    elif args.command == "syncdict":
        logging.info("还没有实现该功能！！！")
        return
        for dict_item in dictionary:
            if mode=="json":
                refs = dict_item.get("json_refs",[])
            elif mode=="html":
                refs = dict_item.get("html_refs",[])
            else :
                refs = dict_item.get("markdown_refs",[])
            new_refs = []
            for ref in refs:
                ref_item_url_id = ref.get("url_id")
                if ref_item_url_id != url_hash:
                    new_refs.append(ref)
            refs = new_refs.copy()        
        FileLib.dumpJson("dictionary.json",dictionary)         
    elif args.command == "cleartask":
        url_hash = args.url_hash
        url = args.url
        url_file = args.url_file
        url_ids = []
        block_idxs = args.block if args.block else []
        only_final = args.only_final
        if not url and not url_hash and not url_file:
            logging.info("必须指定url_hash或者url,或者url_file!")
            return
        if url_hash:
            url_ids = [url_hash]
        elif url:
            url_hash = HashLib.md5(url)
            url_ids = [url_hash]
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
                FileLib.rmdir(f"temp/{url_id}/{mode}")
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
                        if ref_item_url_id != url_id:
                            new_refs.append(ref)
                    #print(f"dict_hash:{dict_hash},url_hash:{url_hash},new_refs:{new_refs.copy()},")
                    refs = new_refs.copy() 
                    if mode=="json":
                        dict_item["json_refs"] = refs
                    elif mode=="html":
                        dict_item["html_refs"] = refs
                    else :
                        dict_item["markdown_refs"] = refs       
            FileLib.dumpJson("dictionary.json",dictionary) 
        except Exception as e:
            logging.info("清除任务失败!"+str(e)) 
if __name__ == "__main__":
    # python3 ../../fix.py --mode json fixdict --dict_hash b614b4 --text="一条消息由消息头和消息体组成。以下部分专注于消息体结构。有关消息头结 构，请参阅："
    # python3 ../../fix.py --mode json cleartask --url_hash d2a41fe3fc36fe7e998e88623d2889a8
    main()