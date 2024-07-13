import traceback
from typing import List, Tuple
from logger import logger
from tqdm import tqdm
import re
import time
import os
import textwrap
import bs4
from bs4 import Doctype

from ylz_translate import Translater, MarkdonwAction, ImageAction
from ylz_translate.utils.crypto_utils import HashLib
from ylz_translate.utils.file_utils import FileLib
from ylz_translate.utils.langchain_utils import LangchainLib
from ylz_translate.utils.soup_utils import SoupLib
from ylz_translate.utils.data_utils import Color, JsonLib, StringLib, UrlLib

class LakeTranslater(Translater):
    def __init__(self,url,crawlLevel=1,markdownAction=MarkdonwAction.JINA):
        super().__init__(url=url,crawlLevel=crawlLevel,markdownAction=markdownAction)
    def get_chain(self):        
        llm = self.langchainLib.get_llm("LLM.TOGETHER")
        systemPromptText = self.config.get("PROMPT.LAKE_MODE")
        prompt = self.langchainLib.get_prompt(textwrap.dedent(systemPromptText))
        #outputParser = self.langchainLib.get_outputParser()
        chain = prompt | llm
        return chain

    def update_dictionary(self, origin_value_dict,target_soup,url_id,block_idx,mask_key="__m__"):
        logger.debug(f"1. enter function,url_id:{url_id},block_idx:{block_idx}")
        for idx, target_element in enumerate(target_soup.find_all(lambda tag:tag.get("t") and tag.get("value"))):
            target_html = "".join([f"<!DOCTYPE {str(item)}>" if isinstance(item,Doctype) else str(item) for item in target_element.contents])
            logger.debug(f"4. idx: {idx},target_text : {target_html}")
            if not re.findall(f"{mask_key}=(.{{6}})",target_html):
                value_hash = target_element.get("value")
                origin_html = origin_value_dict[value_hash]
                logger.debug(f"5.1 hash={value_hash},url_id={url_id},block_idx={block_idx}")
                if not self.dictionary.get(value_hash):
                    self.dictionary[value_hash] = {"origin_text":origin_html,"target_text":target_html,"lake_refs":[]}
                    if url_id!=None and block_idx!=None:
                        self.dictionary[value_hash]["lake_refs"].append({"url_id":url_id,"block_idx":block_idx})
            else:
                value_hash = re.findall(f"{mask_key}=(.{{6}})",target_html)[0]
                logger.debug(f"5.2 hash={value_hash},url_id={url_id},block_idx={block_idx}")
                if self.dictionary.get(value_hash):
                    logger.debug(f"5.3 ")
                    if url_id!=None and block_idx!=None:
                        logger.debug(f"5.4 ")
                        exits = False
                        if "lake_refs" not in self.dictionary[value_hash]:
                            logger.debug(f'5.5 关键错误{not hasattr(self.dictionary[value_hash],"lake_refs")}')
                            self.dictionary[value_hash]["lake_refs"]=[]
                        for item in self.dictionary[value_hash]["lake_refs"]:
                            logger.debug(f"5.6 item['url_id']:{item['url_id']},{url_id};item['block_idx']:{item['block_idx']},{block_idx}")
                            if item["url_id"] == url_id and item["block_idx"]==block_idx:
                                exits = True
                        logger.debug(f"6. url_id & block_idx is exists? {exits}")
                        if not exits:
                            logger.debug(f"7. value_hash={value_hash},url_id = {url_id},block_idx={block_idx}")
                            self.dictionary[value_hash]["lake_refs"].append({"url_id":url_id,"block_idx":block_idx})  
        #FileLib.dumpJson("test.json",self.dictionary)
    def translate_lake_text(self,url_id,chain,lake_data,size=1000):
        newBlocks = []  
        if FileLib.existsFile(f"temp/{url_id}/lake/source.html"):
            source = FileLib.readFile(f"temp/{url_id}/lake/source.html")
            frame = FileLib.readFile(f"temp/{url_id}/lake/frame.html")
            soup = SoupLib.html2soup(frame)
            keep_dict = FileLib.loadJson(f"temp/{url_id}/lake/keep_dict.json")
            attribute_dict = FileLib.loadJson(f"temp/{url_id}/lake/attribute_dict.json")
            value_dict = FileLib.loadJson(f"temp/{url_id}/lake/value_dict.json")
            file_contents = FileLib.readFiles(f"temp/{url_id}/lake","part_[0-9]*_en.html")
            blocks = [ item[1] for item in sorted(file_contents.items())]     
        else:
            lake_keys = self.config.get("LAKE_KEYS")
                
            #将每一个updates的value进行attribue hash
            attribute_dict ={}

            soup = SoupLib.html2soup(lake_data)
            lake_tags = self.config.get("LAKE_TAG")
            for tag in lake_tags:
                SoupLib.replace_tag_name(soup,tag["key"],tag["value"])
            FileLib.writeFile(f"temp/{url_id}/lake/tags.html",SoupLib.soup2html(soup))
            
            attribute_dict.update(SoupLib.hash_attribute(soup))
            source = SoupLib.soup2html(soup)
        
            keep_dict = {}
            lake_keep = self.config.get("LAKE_KEEP")
            if not lake_keep:
                lake_keep = []
            for keep_item in lake_keep:
                keep_dict[HashLib.md5(keep_item)[:6]] = keep_item
            
            blocks = []
            value_dict = {}
            SoupLib.walk(soup, size=size,blocks=blocks,ignore_tags=["script", "style", "ignore","svg"],value_dict = value_dict)
            FileLib.writeFile(f"temp/{url_id}/lake/frame.html",SoupLib.soup2html(soup))
            FileLib.writeFile(f"temp/{url_id}/lake/source.html",source)
            FileLib.dumpJson(f"temp/{url_id}/lake/keep_dict.json",keep_dict)
            FileLib.dumpJson(f"temp/{url_id}/lake/attribute_dict.json",attribute_dict)
            FileLib.dumpJson(f"temp/{url_id}/lake/value_dict.json",value_dict)
            
            for idx,block in enumerate(blocks):
                FileLib.writeFile(f"temp/{url_id}/lake/part_{str(idx).zfill(3)}_en.html",block)

        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                if FileLib.existsFile(f"temp/{url_id}/lake/part_{str(index).zfill(3)}_cn.html"):
                    content = FileLib.readFile(f"temp/{url_id}/lake/part_{str(index).zfill(3)}_cn.html")
                    newBlocks.append(content)
                    pbar.update(1)
                else:
                    try:
                        logger.debug(f"1. block:{block},index:{index}")
                        soup_block = SoupLib.html2soup(block)
                        SoupLib.mask_html_with_dictionary(soup_block,attrs=["t","value"],value_key="value",dictionary = self.dictionary)
                        #SoupLib.mask_text_with_dictionary(soup_block,self.dictionary)
                        
                        #logger.debug(f"2. masked soup: {SoupLib.soup2html(soup_block)}")
                        #logger.debug(f"3. find_all_text_without_mask:{SoupLib.find_all_text_without_mask(soup_block)}")
                        #FileLib.writeFile(f"temp/{url_id}/json/{index}.html",SoupLib.soup2html(soup_block))
                        if SoupLib.find_all_text_without_mask(soup_block):
                            block_replaced = SoupLib.soup2html(soup_block)
                            #StringLib.logging_in_box(f"翻译前no keep:\n{block_replaced}",print_func=print)
                            
                            for keep_key,keep_value in keep_dict.items():
                                block_replaced = block_replaced.replace(keep_value,f"__##k={keep_key}##__")
 
                            #StringLib.logging_in_box(f"翻译前with keep:\n{block_replaced}",print_func=print)
                            
                            logger.info(f"DEBUG:block-idx:{index},block-length:{len(block_replaced)}")
                            result = chain.invoke(
                                {
                                    "input": block_replaced,
                                }
                            )
                            content = result.content
                            for keep_key,keep_value in keep_dict.items():
                                content = content.replace(f"__##k={keep_key}##__",keep_value)
 
                            #StringLib.logging_in_box(f"翻译后no keep:\n{content}",print_func=print)
                            
                            new_soup_block = SoupLib.html2soup(content)
                        else:
                            new_soup_block = soup_block
                        
                        self.update_dictionary(value_dict,new_soup_block,url_id=url_id,block_idx=index)
                        
                        #SoupLib.unmask_text_with_dictionary(new_soup_block,self.dictionary)
                        SoupLib.unmask_html_with_dictionary(new_soup_block,attrs=["t","value"],value_key="value",dictionary=self.dictionary)
                        new_block = SoupLib.soup2html(new_soup_block)
                        #logger.debug(f"4. new_block:{new_block}")
                        FileLib.writeFile(f"temp/{url_id}/lake/part_{str(index).zfill(3)}_cn.html",new_block)
                        newBlocks.append(new_block)
                        pbar.update(1)
                    except Exception as e:
                        logger.info(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                        raise e
        # soup = SoupLib.restore_block_with_dict(soup,keep_dict,"keep")
        SoupLib.unwalk(soup,newBlocks)
        lake_tags = self.config.get("LAKE_TAG")
        for tag in lake_tags:
            SoupLib.replace_tag_name(soup,tag["value"],tag["key"])
        #FileLib.writeFile(f"temp/{url_id}/lake/tags.html",SoupLib.soup2html(soup))
        SoupLib.unhash_attribute(soup,attribute_dict)
        new_updates = SoupLib.soup2html(soup)

        FileLib.writeFile(f"temp/{url_id}/lake/new_updates.html",new_updates)   
        return new_updates
    def start(self, size=1500):
        total = len(self.url)
        logger.info(f"begin on {total} urls")
        startTime = time.time()
        chain = self.get_chain()
        success_files =[]
        exists_files=[]
        error_files=[]
        endTime = time.time() - startTime
        for index,url in enumerate(tqdm(self.url,desc=f"{Color.LYELLOW}总进度{Color.RESET}")):
            try:
                id = HashLib.md5(url)
                FileLib.mkdir(f"temp/{id}/lake")
                taskItem = self.task.get(id)
                if not taskItem:
                    taskItem = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
                    self.task[id] = taskItem
                _,url_type = UrlLib.urlify(url)
                if url_type=="file":
                    lake_file = UrlLib.strip_protocol(url)
                    taskItem["lake"] = lake_file
                lake_file = taskItem.get("lake","")

                if taskItem.get('errorMsg'):
                    error_files.append(f"{id}_cn.lake ---> {lake_file} ---> {url}")
                    logger.info(f"skip on url={url},id={id} ,because it is error ")
                    continue
                if not os.path.exists(f"{id}.lake"):
                    logger.info(f"没有发现json文件 url= {url},id={id} ...")
                    if lake_file:
                        originLake = FileLib.readFile(lake_file)
                        if originLake:
                            FileLib.writeFile(f"{id}.lake",originLake)
                        else:
                            error_files.append(f"{id}_cn.lake ---> {lake_file} ---> {url}")
                            continue
                    else:
                        error_files.append(f"{id}_cn.lake ---> {lake_file} ---> {url}")
                        continue
                else:
                    originLake = FileLib.readFile(f"{id}.lake")
                resultLake = None
                if not os.path.exists(f"{id}_cn.lake"):
                    logger.info(f"开始翻译 url= {url},id={id} ...")
                    resultLake = self.translate_lake_text(id,chain,originLake,size=size)
                    FileLib.writeFile(f"{id}_cn.lake",resultLake)
                    success_files.append(f"{id}_cn.lake ---> {lake_file} ---> {url}")
                else:
                    exists_files.append(f"{id}_cn.lake ---> {lake_file} ---> {url}")
                    resultLake = FileLib.readFile(f"{id}_cn.lake")
                
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                error_files.append(f"{id}_cn.lake ---> {lake_file} ---> {url}")
                taskItem["errorMsg"] = str(e)
                logger.info(f"error on url={url},id={id},error={str(e)}")
                traceback.print_exc()
                #raise e
            FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        

        FileLib.writeFile("files_success.txt","\n".join(success_files))
        FileLib.writeFile("files_exists.txt","\n".join(exists_files))
        FileLib.writeFile("files_error.txt","\n".join(error_files))
        FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        FileLib.dumpJson(self.taskFilename,self.task)
        logger.info("="*80)
        files_str = '\n'.join(success_files)
        logger.info(f"success_files:\n{files_str}")
        files_str = '\n'.join(exists_files)
        logger.info(f"exists_files:\n{files_str}")
        files_str = '\n'.join(error_files)
        logger.info(f"error_files:\n{files_str}")
        logger.info("-"*50)
        logger.info(f"本次任务共耗时:{round(endTime/60,2)}分钟。成功:{len(success_files)}条，已存在:{len(exists_files)}条，失败:{len(error_files)}条")
        logger.info("="*80)
        