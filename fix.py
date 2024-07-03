
import logging
import os
import sys
import argparse
import re

from translate.utils.file_utils import FileLib
from translate.utils.crypto_utils import HashLib

def main():
    parser = argparse.ArgumentParser(description = "维护工具")
    parser.add_argument("--mode", required=True, choices=["markdown","html","json"],help="处理模式(markdown|html|json)")
    
    subparsers = parser.add_subparsers(dest="command", help="使用子命令")

    fixDict_parser = subparsers.add_parser("fixDict", help="根据hash或文本特征更新相应字典，以便渐进式翻译")
    fixDict_parser.add_argument("--dict_hash", required=False, help="字典的hash值(6位)")
    fixDict_parser.add_argument("--issubtext", action="store_true",required=False, help="是否是部分文字片段")
    fixDict_parser.add_argument("--old_text",required=False,help="字典中目标文本或者是所包含的文字片段正则表达式，这取决于--issubtext。注意：如果是文字片段正则表达式则应有足够的特征以避免大范围错误更新")
    fixDict_parser.add_argument("--new_text",required=True,help="如果指定字典的hash且--issubtext不为True，则--new_text应为完整的文本；如果指定或--old_text则--new_text指所对应的文字，这取决于--issubtext")
    fixDict_parser.add_argument("-l","--only_list", action="store_true",required=False, help="仅查看，不更改字典和删除文件")
    fixDict_parser.add_argument("--url_ids", nargs="*",type=str,required=False, help="限定字典ref包含url_id的列表内容")
    fixDict_parser.add_argument("--origin_text", type=str,required=False, help="限定字典原始值包含--origin_text正则")
 
    syncDict_parser = subparsers.add_parser("syncDict", help="同步字典")
    syncDict_parser.add_argument("--dict_hash", required=True, help="字典的hash值(6位)")
    
    clearTask_parser = subparsers.add_parser("clearTask", help="清除已完成的url翻译,以便重新翻译")
    clearTask_parser.add_argument("--url_id",help="任务的url id值(32位)")
    clearTask_parser.add_argument("--url", help="任务的url,如果同时指定了--ulr_id则忽略此参数")
    clearTask_parser.add_argument("-f","--url_file",type=str,help="包含一行或多行url的文件,指定--url或--url_id时忽略此参数")
    clearTask_parser.add_argument("--blocks",nargs="*",type=int,help="要删除的block index列表,如--blocks 1 3 5")
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
    
    if args.command == "fixDict":    
        dict_hash = args.dict_hash
        issubtext = args.issubtext
        dict_old_text = args.old_text
        dict_new_text = args.new_text
        only_list = args.only_list
        url_ids = args.url_ids
        origin_text_pattern = args.origin_text

        if (dict_hash==None and dict_old_text==None) or (dict_hash!=None and dict_old_text!=None):
            logging.info("必须指定--dict_hash和--old_text中的一个!")
            return
        if len(dict_new_text)==0:
            logging.info("请指定字典的hash所对应的--new_text!")
            return
        if dict_hash!=None and issubtext==True:
            logging.info("字典hash模式下--issubtext必须为False!")
            return
        if dict_hash!=None and len(dict_hash)!=6:
            logging.info("字典的hash值必须位6位!")
            return

        dict_hashs = []
        if dict_hash!=None:
            dict_hashs = [dict_hash]
            dict_item = dictionary.get(dict_hash)
            old_target_text = dict_item.get("target_text")
            old_origin_text = dict_item.get("origin_text")
            if only_list:
                if mode=="json":
                    refs = dict_item.get("json_refs",[])
                elif mode=="html":
                    refs = dict_item.get("html_refs",[])
                else :
                    refs = dict_item.get("markdown_refs",[])
                ref_info = []
                for ref in refs:
                     if len(url_ids)==0 or ref.get("url_id") in url_ids:
                         ref_info.append(f"{ref['url_id']}-{ref['block_idx']}")
                if ref_info and re.match(origin_text_pattern,old_origin_text):
                    logging.info(f"字典hash:{dict_hash}")
                    logging.info(f"ref_url_ids:,{ref_info}")
                    logging.info(f"原文本:{old_target_text}")
                    logging.info(f"新文本:{dict_new_text}")    
        else:
            for dict_hash in dictionary:
                dict_item = dictionary.get(dict_hash)
                old_target_text = dict_item.get("target_text")
                if mode=="json":
                    refs = dict_item.get("json_refs",[])
                elif mode=="html":
                    refs = dict_item.get("html_refs",[])
                else :
                    refs = dict_item.get("markdown_refs",[])
                ref_info = []
                for ref in refs:
                     if len(url_ids)==0 or ref.get("url_id") in url_ids:
                         ref_info.append(f"{ref['url_id']}-{ref['block_idx']}")
                if ref_info and re.match(origin_text_pattern,old_origin_text):
                    if not issubtext:
                        if old_target_text == dict_old_text:
                            dict_hashs.append(dict_hash)
                            idx = len(dict_hashs)
                            if only_list:            
                                logging.info(f"{idx}.字典hash:{dict_hash}")
                                logging.info(f"ref_url_ids:{ref_info}")
                                logging.info(f"原文本:{old_target_text}")
                                logging.info(f"新文本:{dict_new_text}")
                    else:
                        pattern = dict_old_text
                        if re.match(pattern, old_target_text):
                            dict_hashs.append(dict_hash)
                            idx = len(dict_hashs)
                            if only_list:
                                text = re.findall(pattern,old_target_text)[0]
                                left = old_target_text.find(text)
                                right = left + len(text)
                                left_begin = left - 20 if left>20 else 0
                                right_end = right + 20 if right+20<len(old_target_text) else len(old_target_text)
                                logging.info(f"{idx}.字典hash:{dict_hash}")
                                logging.info(f"ref_url_ids:{ref_info}")
                                logging.info(f"原文本:...{old_target_text[left_begin:left]}【{text}】{old_target_text[right:right_end]}...")
                                logging.info(f"新文本:...{dict_new_text}...")
            logging.info(f"找到{len(dict_hashs)}个字典hash\n{dict_hashs}")
        if only_list:
            return
        try:
            for dict_hash in dict_hashs:
                dict_item = dictionary.get(dict_hash)
                if not dict_item:
                    logging.info(f"没有找到字典hash={dict_hash}的数据!")
                    return
                origin_text = dict_item.get("origin_text")
                old_target_text = dict_item.get("target_text")
                if not issubtext:
                    dict_item["target_text"] = dict_new_text
                else:
                    text = re.findall(dict_old_text,old_target_text)[0]
                    dict_item["target_text"] = old_target_text.replace(text,dict_new_text)
                shrink_origin_text = origin_text.replace("\n","")
                #logging.info(f"将字典hash={dict_hash}的目标文字\n由【{old_target_text}】\n改为【{dict_item['target_text']}】\n原始文字为:【{shrink_origin_text}】")

                if mode=="json":
                    refs = dict_item.get("json_refs",[])
                elif mode=="html":
                    refs = dict_item.get("html_refs",[])
                else :
                    refs = dict_item.get("markdown_refs",[])
                for ref in refs:
                    ref_item_url_id = ref.get("url_id")
                    if len(url_ids)==0 or (ref_item_url_id in url_ids):
                        ref_item_block_idx = ref.get("block_idx")
                        #logging.info(f"???,dict_hash={dict_hash},ref_item_url_id={ref_item_url_id},ref_item_block_idx={ref_item_block_idx}")
                        if ref_item_url_id!=None and ref_item_block_idx!=None:
                            FileLib.rmFile(f"temp/{ref_item_url_id}/{mode}/part_{str(ref_item_block_idx).zfill(3)}_cn.html")
                            FileLib.rmFile(f"{ref_item_url_id}_cn.{mode_fix}")            
            FileLib.dumpJson("dictionary.json",dictionary)
        except Exception as e:
            logging.info("更新字典失败!"+str(e))

    elif args.command == "syncDict":
        logging.info("还没有实现该功能！！！")
        return
    elif args.command == "clearTask":
        url_id = args.url_id
        url = args.url
        url_file = args.url_file
        url_ids = []
        block_idxs = args.blocks if args.blocks else []
        only_final = args.only_final
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
                    
            FileLib.dumpJson("dictionary.json",dictionary) 
        except Exception as e:
            logging.info("清除任务失败!"+str(e)) 
if __name__ == "__main__":
    # python3 ../../fix.py --mode json fixDict --dict_hash b614b4 --new_text="一条消息由消息头和消息体组成。以下部分专注于消息体结构。有关消息头结 构，请参阅："
    # python3 ../../fix.py --mode json fixDict --old_text "abcde" --new_text="ABCDE"
    # python3 ../../fix.py --mode json clearTask --url_id d2a41fe3fc36fe7e998e88623d2889a8 --blocks 1 3 5
    # python3 ../../fix.py --mode json fixDict --old_text "<.+>(.*消息由.*?)</.+>" --new_text "报文由报文头和报文正文组成。以下部 分专注于报文正文结构。报文头结构请参阅" --issubtext
    main()