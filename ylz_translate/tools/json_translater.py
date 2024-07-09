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
from ylz_translate.utils.data_utils import Color, JsonLib, UrlLib

class JsonTranslater(Translater):
    def __init__(self,url,crawlLevel=1,markdownAction=MarkdonwAction.JINA):
        super().__init__(url=url,crawlLevel=crawlLevel,markdownAction=markdownAction)
        self.langchainLib = LangchainLib()
    def get_chain(self):
        print("????",self.config)
        base_url = self.config.get("LLM.TOGETHER.BASE_URL","https://api.together.xyz/v1")
        api_key:str = self.config.get("LLM.TOGETHER.API_KEY"),
        model= self.config.get("LLM.TOGETHER.MODEL","Qwen/Qwen1.5-72B-Chat")
        print(type(model),model)
        print(type(api_key),api_key)

        if type(api_key) in [list,tuple]:
            api_key = api_key[0]
        llm = self.langchainLib.get_chatopenai_llm(
            base_url= base_url,
            api_key= api_key,
            model= model,temperature=0)
        # llm = get_chatopenai_llm(
        #     api_key= self.config.get("LLM",{}).get("SILICONFLOW_API_KEY"),
        #     base_url="https://api.siliconflow.cn/v1",
        #     #model="alibaba/Qwen2-57B-A14B-Instruct",
        #     model="alibaba/Qwen1.5-110B-Chat",
        #     temperature=0)
    #     systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务及技术接口,擅长这些方面的技术文档的翻译。
    # 现在请将下面的HTML格式的英文文本全部翻译成中文,输出HTML文档,不要做任何解释。输出格式为```html ...```
    # 请始终使用以下逗号分隔的术语对应列表进行翻译,（如果术语表的key与value一致则表示key的值保持原样）。术语对应表如下：
    # [message:报文,redirection URL:跳转链接,payment continuation URL:支付推进链接,reconstructed redirection URL:重构后的重定向链接,Alipay+ MPP:Alipay+ 支付方式,
    #  Antom Dashboard:Antom Dashboard,secondary merchant:二级商户,acquirer:收单机构,URL scheme:URL scheme,access token:访问令牌,refresh token:刷新令牌,
    #  signature:签名,private key:私钥,public key:公钥,vaulting:绑定,card vaulting:绑卡,co-badged card:双标卡,issuing bank:发卡行,capture:请款,the request traffic:请求流量,	
    #  response header:响应头,response body:响应体,scope:作用域,idempotence:幂等性,anti-money laundering:反洗钱,purchase tracking:采购追踪,regulatory reporting:监管报告,
    #  payment session data:支付会话数据,dispute:争议,chargeback:拒付,declare:海关报关,expiration time:有效期,default time:预设时间,asynchronous notification:异步通知,
    #  API:接口,Antom:Antom,Alipay:Antom,Antom Merchant Portal:Antom Merchant Portal,Antom Dashboard:Antom Dashboard,Boolean:布尔属性,Integer:整数属性,array:数组]

    # 特别要求:
    #     1、尽量理解标签结构及上下文，该翻译的尽量翻译，不要有遗漏,简单明了
    #     2、禁止翻译代码中的非注释内容
    #     3、表格中全部大写字母的为错误代码，禁止翻译
    #     4、保持所有原始的HTML标签格式及结构，特别是<code>标签及其内容
    #     5、检查翻译的结果,以确保语句通顺
    # """
        systemPromptText = self.config.get("PROMPT.JSON_MODE")
        prompt = self.langchainLib.get_prompt(textwrap.dedent(systemPromptText))
        chain = prompt | llm
        return chain

    def update_dictionary(self, origin_value_dict,target_soup,url_id,block_idx,mask_key="__m__"):
        logger.debug(f"1. enter function,url_id:{url_id},block_idx:{block_idx}")
        for idx, target_element in enumerate(target_soup.find_all(lambda tag:tag.get("path") and tag.get("value"))):
            target_html = ''.join([str(item) for item in target_element.contents])
            logger.debug(f"4. idx: {idx},target_text : {target_html}")
            if not re.findall(f"{mask_key}=(.{{6}})",target_html):
                value_hash = target_element.get("value")
                origin_html = origin_value_dict[value_hash]
                logger.debug(f"5.1 hash={value_hash},url_id={url_id},block_idx={block_idx}")
                if not self.dictionary.get(value_hash):
                    self.dictionary[value_hash] = {"origin_text":origin_html,"target_text":target_html,"json_refs":[]}
                    if url_id!=None and block_idx!=None:
                        self.dictionary[value_hash]["json_refs"].append({"url_id":url_id,"block_idx":block_idx})
                else:
                    logger.debug(f"6????")
            else:
                value_hash = re.findall(f"{mask_key}=(.{{6}})",target_html)[0]
                logger.debug(f"5.2 hash={value_hash},url_id={url_id},block_idx={block_idx}")
                if self.dictionary.get(value_hash):
                    logger.debug(f"5.3 ")
                    if url_id!=None and block_idx!=None:
                        logger.debug(f"5.4 ")
                        exits = False
                        if "json_refs" not in self.dictionary[value_hash]:
                            logger.debug(f'5.5 关键错误{not hasattr(self.dictionary[value_hash],"json_refs")}')
                            self.dictionary[value_hash]["json_refs"]=[]
                        for item in self.dictionary[value_hash]["json_refs"]:
                            logger.debug(f"5.6 item['url_id']:{item['url_id']},{url_id};item['block_idx']:{item['block_idx']},{block_idx}")
                            if item["url_id"] == url_id and item["block_idx"]==block_idx:
                                exits = True
                        logger.debug(f"6. url_id & block_idx is exists? {exits}")
                        if not exits:
                            self.dictionary[value_hash]["json_refs"].append({"url_id":url_id,"block_idx":block_idx})  
        #FileLib.dumpJson("test.json",self.dictionary)
    def split_json_and_replace_struct(self, json_data_list, size) -> Tuple[List[str],dict,dict]:
        length =0
        blocks=[]
        block_items=[]
        for item in json_data_list:
            item_len = len(item["value"])
            #logger.info(f'{len(blocks)},{len(block_items)},{length},{size},{len(item["value"])},{"/".join([str(p) for p in item["path"]])}')
            if length + item_len > size:
                blocks.append(block_items.copy())
                block_items=[]
                block_items.append(item)
                length = item_len
            else:
                block_items.append(item)
                length += item_len
        if block_items:
            blocks.append(block_items.copy())
        
        path_dict = {}
        value_dict = {}
        restruct_blocks=[]
        for block_items in blocks:
            html = ""
            for block in block_items:
                path_hash = HashLib.md5("/".join([str(item) for item in block["path"]]))[:6]
                path_dict[path_hash] = block["path"]
                value_hash = HashLib.md5(block["value"])[:6]
                value_dict[value_hash] = block["value"]
                html += f"<div path={path_hash} value={value_hash}>{block['value']}</div>"
            restruct_blocks.append(html)
            #restruct_block = SoupLib.wrap_block_with_tag(SoupLib.html2soup(html,"html.parser"),"div")
            #restruct_blocks.append(restruct_block)              
        return restruct_blocks,path_dict,value_dict    
    def restore_struct_and_join_json(self,html_data_list:list[list[str]],path_dict:dict) -> List[dict]:
        # html_data_list example:
        # ["<div path="33b031"><p>abc</p> </div>
        #   <div path="33b032"><p>123</p> </div>",
        #  "<div path="33b033"><p>xyz</p> </div>
        #   <div path="33b034"><p>456</p> </div>",
        # ]
        new_updates = []
        for html_data in html_data_list:
            soup_data = SoupLib.html2soup(html_data)
            contents = soup_data.contents
            for content in contents:
                if type(content) == bs4.element.NavigableString and content.text=="\n":
                    continue
                content_hash = content.attrs.get("path")
                if content_hash:
                    path = path_dict.get(content_hash)
                    if path:
                        value = "".join([f"<!DOCTYPE {str(item)}>" if isinstance(item,Doctype) else str(item) for item in content.contents])
                        new_updates.append({"value":value,"path":path})
        return new_updates                    
    def translate_json_text(self,url_id,chain,json_data,size=1000):
        newBlocks = []  
        if FileLib.existsFile(f"temp/{url_id}/json/source.json"):
            updates = FileLib.loadJson(f"temp/{url_id}/json/source.json")
            keep_dict = FileLib.loadJson(f"temp/{url_id}/json/keep_dict.json")
            attribute_dict = FileLib.loadJson(f"temp/{url_id}/json/attribute_dict.json")
            path_dict = FileLib.loadJson(f"temp/{url_id}/json/path_dict.json")
            value_dict = FileLib.loadJson(f"temp/{url_id}/json/value_dict.json")
            file_contents = FileLib.readFiles(f"temp/{url_id}/json","part_[0-9]*_en.html")
            blocks = [ item[1] for item in sorted(file_contents.items())]     
        else:
            updates=[]
            json_keys = self.config.get("JSON_KEYS")
            for json_key in json_keys:
                updates += JsonLib.find_key_value_path(json_data,json_key)
            # updates += JsonLib.find_key_value_path(json_data,"description") #descriptionLake
            # updates += JsonLib.find_key_value_path(json_data,"descriptionLake")
            # updates += JsonLib.find_key_value_path(json_data,"x-result.[].message")
            # updates += JsonLib.find_key_value_path(json_data,"x-result.[].action") #actionLake
            # updates += JsonLib.find_key_value_path(json_data,"x-result.[].actionLake")
            # updates += JsonLib.find_key_value_path(json_data,"x-more") #x-more-lake
            # updates += JsonLib.find_key_value_path(json_data,"x-more-lake")
            # updates += JsonLib.find_key_value_path(json_data,"x-idempotencyDescription")
            # updates += JsonLib.find_key_value_path(json_data,"x-warning") #x-warning-lake
            # updates += JsonLib.find_key_value_path(json_data,"x-warning-lake")
            # updates += JsonLib.find_key_value_path(json_data,"x-range")
            # updates += JsonLib.find_key_value_path(json_data,"x-notAllowed")
            
            #过滤空字符串
            updates = [item for item in updates if item["value"]]
                
            #将每一个updates的value进行attribue hash
            attribute_dict ={}
            FileLib.dumpJson(f"temp/{url_id}/json/source1.json",updates)
            for item in updates:
                #对于&lt;,&gt;转化为<>标签
                item["value"] = item["value"].replace("&lt;","<").replace("&gt;",">")
                soup = SoupLib.html2soup(item["value"])
                attribute_dict.update(SoupLib.hash_attribute(soup))
                item["value"] = SoupLib.soup2html(soup)
            
            keep_dict = {}
            json_keep = self.config.get("JSON_KEEP")
            if not json_keep:
                json_keep = []
            for keep_item in json_keep:
                keep_dict[HashLib.md5(keep_item)[:6]] = keep_item

            blocks,path_dict,value_dict = self.split_json_and_replace_struct(updates,size)
            FileLib.dumpJson(f"temp/{url_id}/json/source.json",updates)
            FileLib.dumpJson(f"temp/{url_id}/json/keep_dict.json",keep_dict)
            FileLib.dumpJson(f"temp/{url_id}/json/attribute_dict.json",attribute_dict)
            FileLib.dumpJson(f"temp/{url_id}/json/path_dict.json",path_dict)
            FileLib.dumpJson(f"temp/{url_id}/json/value_dict.json",value_dict)
            for idx,block in enumerate(blocks):
                FileLib.writeFile(f"temp/{url_id}/json/part_{str(idx).zfill(3)}_en.html",block)
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                if FileLib.existsFile(f"temp/{url_id}/json/part_{str(index).zfill(3)}_cn.html"):
                    content = FileLib.readFile(f"temp/{url_id}/json/part_{str(index).zfill(3)}_cn.html")
                    newBlocks.append(content)
                    pbar.update(1)
                else:
                    try:
                        logger.debug(f"1. block:{block},index:{index}")
                        soup_block = SoupLib.html2soup(block)
                        SoupLib.mask_html_with_dictionary(soup_block,attrs=["path","value"],value_key="value",dictionary = self.dictionary)
                        #SoupLib.mask_text_with_dictionary(soup_block,self.dictionary)
                        
                        #logger.debug(f"2. masked soup: {SoupLib.soup2html(soup_block)}")
                        #logger.debug(f"3. find_all_text_without_mask:{SoupLib.find_all_text_without_mask(soup_block)}")
                        #FileLib.writeFile(f"temp/{url_id}/json/{index}.html",SoupLib.soup2html(soup_block))
                        if SoupLib.find_all_text_without_mask(soup_block):
                            block_replaced = SoupLib.soup2html(soup_block)
                            # fix bug 为什么要剔除这个，不剔除语言模型必然出错，怪哉????
                            # logger.info("?"*80)
                            # logger.info(block_replaced)
                            # logger.info("?"*80)
                            
                            for keep_key,keep_value in keep_dict.items():
                                block_replaced = block_replaced.replace(keep_value,f"__##k={keep_key}##__")
                            # logger.info("="*80)
                            # logger.info(block_replaced)
                            # logger.info("="*80)
                            
                            logger.info(f"DEBUG:block-idx:{index},block-length:{len(block_replaced)}")
                            result = chain.invoke(
                                {
                                    "input": block_replaced,
                                }
                            )
                            content = result.content
                            for keep_key,keep_value in keep_dict.items():
                                content = content.replace(f"__##k={keep_key}##__",keep_value)
                            # logger.info("="*80)
                            # logger.info(content)
                            # logger.info("="*80)
                            
                            new_soup_block = SoupLib.html2soup(content)
                        else:
                            new_soup_block = soup_block
                        self.update_dictionary(value_dict,new_soup_block,url_id=url_id,block_idx=index)
                        #SoupLib.unmask_text_with_dictionary(new_soup_block,self.dictionary)
                        SoupLib.unmask_html_with_dictionary(new_soup_block,attrs=["path","value"],value_key="value",dictionary=self.dictionary)
                        new_block = SoupLib.soup2html(new_soup_block)
                        #logger.debug(f"4. new_block:{new_block}")
                        FileLib.writeFile(f"temp/{url_id}/json/part_{str(index).zfill(3)}_cn.html",new_block)
                        newBlocks.append(new_block)
                        pbar.update(1)
                    except Exception as e:
                        logger.info(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                        raise e
        
        # soup = SoupLib.restore_block_with_dict(soup,keep_dict,"keep")
        new_updates = self.restore_struct_and_join_json(newBlocks,path_dict)
        #FileLib.dumpJson(f"temp/{url_id}/json/new0_updates.json",new_updates)
        for item in new_updates:
            soup = SoupLib.html2soup(item["value"])
            SoupLib.unhash_attribute(soup,attribute_dict)
            item["value"] = SoupLib.soup2html(soup)

        FileLib.dumpJson(f"temp/{url_id}/json/new_updates.json",new_updates)   
        resultJson = JsonLib.update_json_by_path(json_data,new_updates,lambda value:value)
        return resultJson
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
                FileLib.mkdir(f"temp/{id}/json")
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
                    json_file = UrlLib.strip_protocol(url)
                    taskItem["json"] = json_file
                json_file = taskItem.get("json","")

                if taskItem.get('errorMsg'):
                    error_files.append(f"{id}_cn.json ---> {json_file} ---> {url}")
                    logger.info(f"skip on url={url},id={id} ,because it is error ")
                    continue
                if not os.path.exists(f"{id}.json"):
                    logger.info(f"没有发现json文件 url= {url},id={id} ...")
                    if json_file:
                        originJson = FileLib.loadJson(json_file,encoding="cp1252")
                        if originJson:
                            FileLib.dumpJson(f"{id}.json",originJson)
                        else:
                            error_files.append(f"{id}_cn.json ---> {json_file} ---> {url}")
                            continue
                    else:
                        error_files.append(f"{id}_cn.json ---> {json_file} ---> {url}")
                        continue
                else:
                    originJson = FileLib.loadJson(f"{id}.json")
                resultJson = None
                if not os.path.exists(f"{id}_cn.json"):
                    logger.info(f"开始翻译 url= {url},id={id} ...")
                    resultJson = self.translate_json_text(id,chain,originJson,size=size)
                    FileLib.dumpJson(f"{id}_cn.json",resultJson)
                    success_files.append(f"{id}_cn.json ---> {json_file} ---> {url}")
                else:
                    exists_files.append(f"{id}_cn.json ---> {json_file} ---> {url}")
                    resultJson = FileLib.loadJson(f"{id}_cn.json")
                
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                error_files.append(f"{id}_cn.json ---> {json_file} ---> {url}")
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
        