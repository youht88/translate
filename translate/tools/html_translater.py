from logger import logger
from tqdm import tqdm
import re
import time
import os
import textwrap
import traceback

from translate import Translater, MarkdonwAction, ImageAction
from translate.utils.soup_utils import SoupLib
from translate.utils.crypto_utils import HashLib
from translate.utils.file_utils import FileLib
from translate.utils.playwright_utils import PlaywrightLib
from translate.utils.langchain_utils import LangchainLib

class HtmlTranslater(Translater):
    def __init__(self,url,crawlLevel=1,markdownAction=MarkdonwAction.JINA,env_file=None):
        super().__init__(url=url,crawlLevel=crawlLevel, markdownAction=markdownAction,env_file=env_file)
        self.langchainLib = LangchainLib()
    def get_chain(self):
        llm = self.langchainLib.get_chatopenai_llm(
            base_url="https://api.together.xyz/v1",
            api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
            model="Qwen/Qwen1.5-72B-Chat",temperature=0)
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请将下面的markdown格式文档全部翻译成中文。
        注意:
          1、不要有遗漏,简单明了。
          2、特别不要遗漏嵌套的mardkown的语法
          3、禁止翻译代码中的JSON的key
          4、保留所有空白行,以确保markdown格式正确
          5、检查翻译的结果,以确保语句通顺
        \n\n"""
        prompt = self.langchainLib.get_prompt(textwrap.dedent(systemPromptText))
        chain = prompt | llm
        return chain
    def update_dictionary(self, origin_soup, target_soup,url_id,block_idx,mask_key="__m__"):
        logger.debug(f"1. enter function")
        if SoupLib.compare_soup_structure(origin_soup,target_soup):
            origin_texts = SoupLib.find_all_text(origin_soup)
            target_texts = SoupLib.find_all_text(target_soup)
            logger.debug(f"2. compare soup structure")
            if len(origin_texts) == len(target_texts):
                logger.debug(f"3. length equal {len(origin_texts)}")
                for idx, origin_text in enumerate(origin_texts):
                    target_text = target_texts[idx]
                    logger.debug(f"4. idx: {idx},target_text : {target_text}")
                    if not re.match(f"{mask_key}=(.{{6}})",target_text):
                        hash = HashLib.md5(origin_text)[:6]
                        logger.debug(f"5.1 hash={hash},url_id={url_id},block_idx={block_idx}")
                        if not self.dictionary.get(hash):
                            self.dictionary[hash] = {"origin_text":origin_text,"target_text":target_text,"html_refs":[]}
                            if url_id and block_idx:
                                self.dictionary[hash]["html_refs"].append({"url_id":url_id,"block_idx":block_idx})
                    else:
                        hash = re.findall(f"{mask_key}=(.{{6}})",target_text)[0]
                        logger.debug(f"5.2 hash={hash},url_id={url_id},block_idx={block_idx}")
                        if self.dictionary.get(hash):
                            if url_id and block_idx:
                                exits = False
                                if "html_refs" not in self.dictionary[hash]:
                                    self.dictionary[hash]["html_refs"]=[]
                                for item in self.dictionary[hash]["html_refs"]:
                                    if item["url_id"] == url_id and item["block_idx"]==block_idx:
                                        exits = True
                                logger.debug(f"6. url_id & block_idx is exists? {exits}")
                                if not exits:
                                    self.dictionary[hash]["html_refs"].append({"url_id":url_id,"block_idx":block_idx})  

    def translate_html_text(self,url_id,chain,text,size=1000):
        newBlocks = [] 
        if FileLib.existsFile(f"temp/{url_id}/html/soup.html"):
            html = FileLib.readFile(f"temp/{url_id}/html/soup.html")
            soup = SoupLib.html2soup(html)
            attribute_dict = FileLib.loadJson(f"temp/{url_id}/html/attribute_dict.json")
            keep_dict = FileLib.loadJson(f"temp/{url_id}/html/keep_dict.json")
            file_contents = FileLib.readFiles(f"temp/{url_id}/html","part_[0-9]*_en.html")
            blocks = [ item[1] for item in sorted(file_contents.items())]                  
        else:
            soup = SoupLib.html2soup(text)
            selectors = ['//h4[starts-with(@id,"Requestparameters")]/span[starts-with(@class,"name")]',
                         '//h4[starts-with(@id,"Requestparameters")]/span[starts-with(@class,"type")]',
                         '//h4[starts-with(@id,"Responseparameters")]/span[starts-with(@class,"name")]',
                         '//h4[starts-with(@id,"Responseparameters")]/span[starts-with(@class,"type")]'
            ]
            soup,keep_dict = SoupLib.replace_block_with_tag(soup,"keep",selectors)
            soup = SoupLib.wrap_block_with_tag(soup,"ignore",['//section[contains(@class,"right")]','//aside'])
            attribute_dict = SoupLib.hash_attribute(soup)
            blocks = []
            SoupLib.walk(soup, size=size,blocks=blocks,ignore_tags=["script", "style", "ignore","svg"])
            FileLib.writeFile(f"temp/{url_id}/html/soup.html",SoupLib.soup2html(soup))
            FileLib.dumpJson(f"temp/{url_id}/html/attribute_dict.json",attribute_dict)
            FileLib.dumpJson(f"temp/{url_id}/html/keep_dict.json",keep_dict)
            for idx,block in enumerate(blocks):
                FileLib.writeFile(f"temp/{url_id}/html/part_{str(idx).zfill(3)}_en.html",block)
                
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                if FileLib.existsFile(f"temp/{url_id}/html/part_{str(index).zfill(3)}_cn.html"):
                    content = FileLib.readFile(f"temp/{url_id}/html/part_{str(index).zfill(3)}_cn.html")
                    newBlocks.append(content)
                    pbar.update(1)
                else:
                    try:
                        logger.debug(f"1. block:{block},index:{index}")
                        soup_block = SoupLib.html2soup(block)
                        SoupLib.mask_text_with_dictionary(soup_block,self.dictionary)
                        #logger.debug(f"2. masked soup: {SoupLib.soup2html(soup_block)}")
                        #logger.debug(f"3. find_all_text_without_mask:{SoupLib.find_all_text_without_mask(soup_block)}")
                        if SoupLib.find_all_text_without_mask(soup_block):
                            block_replaced = SoupLib.soup2html(soup_block)
                            result = chain.invoke(
                                {
                                    "input": block_replaced,
                                }
                            )
                            content = result.content
                            new_soup_block = SoupLib.html2soup(content)
                        else:
                            new_soup_block = soup_block
                        self.update_dictionary(soup_block,new_soup_block,url_id=url_id,block_idx=index)
                        SoupLib.unmask_text_with_dictionary(new_soup_block,self.dictionary)
                        new_block = SoupLib.soup2html(new_soup_block)
                        #logger.debug(f"4. new_block:{new_block}")
                        FileLib.writeFile(f"temp/{url_id}/html/part_{str(index).zfill(3)}_cn.html",new_block)
                        newBlocks.append(new_block)
                        pbar.update(1)
                    except Exception as e:
                        logger.info(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                        raise e
        SoupLib.unwalk(soup,newBlocks)
        SoupLib.unhash_attribute(soup,attribute_dict)
        soup = SoupLib.unwrap_block_with_tag(soup,"ignore")
        soup = SoupLib.restore_block_with_dict(soup,keep_dict,"keep")
        resultHtml = soup.prettify("utf-8")
        return resultHtml.decode("utf-8")
    async def get_html(self, url):
        async with PlaywrightLib(headless=False) as pw:
            await pw.goto(url,start_log="开始加载页面",end_log="页面加载完成",wait_until="domcontentloaded",timeout=180000)
            pw.wait(3000,start_log="等待3秒",end_log="等待结束")
            logger.info(await pw.selector_exists('//section[contains(@class,"right")]'))
            request_show = await pw.selector_exists("//div[@id='Requestparameters']//button//span[contains(text(),'Show all')]")
            if request_show:
                await pw.click("//div[@id='Requestparameters']//button//span[contains(text(),'Show all')]",start_log="点击Req Show all按钮")
            response_show = await pw.selector_exists("//div[@id='Responseparameters']//button//span[contains(text(),'Show all')]")
            if response_show:
                await pw.click("//div[@id='Responseparameters']//button//span[contains(text(),'Show all')]",start_log="点击Res Show all按钮")
            pw.wait(3000,start_log="等待3秒",end_log="等待结束")
            if request_show:
                await pw.wait_for_selector("//div[@id='Requestparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Req Hide all按钮")
            if response_show:
                await pw.wait_for_selector("//div[@id='Responseparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Res Hide all按钮")
            html = await pw.get_html()
            #pw.wait(10000,start_log="等待10秒",end_log="等待结束")        
            await pw.close()
            return html[0]

    async def start(self, imageAction:ImageAction|None=None,size=1500,only_download=False):
        total = len(self.url)
        logger.info(f"begin on {total} urls")
        startTime = time.time()
        chain = self.get_chain()
        for index,url in enumerate(self.url):
            try:
                id = HashLib.md5(url)
                FileLib.mkdir(f"temp/{id}/html")
                taskItem = self.task.get(id)
                if not taskItem:
                    taskItem = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
                    self.task[id] = taskItem
                if taskItem.get('errorMsg'):
                    logger.info(f"skip on url={url},id={id} ,because it is error ")
                    continue
                if not os.path.exists(f"{id}.html"):
                    logger.info(f"提取html url= {url},id={id} ...")
                    originHtml = await self.get_html(url)
                    metadata = None
                    if originHtml:
                        FileLib.writeFile(f"{id}.html",originHtml)
                        #image_links = re.findall(r"!\[(.*?)\]\((.*?)\)",originMarkdown)
                        #taskItem["imageLinks"] = list(map(lambda item:[item[0],item[1],HashLib.md5(item[1])],image_links))
                    if metadata:
                        taskItem["metadata"] = metadata
                    taskItem["markdownAction"] = str(self.markdownAction)
                else:
                    originHtml = FileLib.readFile(f"{id}.html")
                resultHtml = None
                if not only_download:
                    if not os.path.exists(f"{id}_cn.html"):
                        logger.info(f"开始翻译 url= {url},id={id} ...")
                        resultHtml = self.translate_html_text(id,chain,originHtml,size=size)
                        FileLib.writeFile(f"{id}_cn.html",resultHtml)
                    else:
                        resultHtml = FileLib.readFile(f"{id}_cn.html")
                
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                taskItem["errorMsg"] = str(e)
                logger.info(f"error on url={url},id={id},error={str(e)}")
                #raise e
        FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        FileLib.dumpJson(self.taskFilename,self.task)
        if imageAction and self.imageTranslater:
            self.imageTranslater.save()       
