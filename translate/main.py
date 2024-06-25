import sys
import time
from urllib.parse import quote, urljoin, urlparse
from markdownify import markdownify
import requests
from bs4 import BeautifulSoup
import re 
import json
import copy
import os
from tqdm import tqdm
import textwrap
# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp
from enum import Enum
import random

from logger import logger
import logging
import asyncio

from utils.file_utils import FileLib
from utils.crypto_utils import HashLib
from utils.langchain_utils import *
from utils.soup_utils import SoupLib
from utils.config_utils import Config
from utils.playwright_utils import PlaywrightLib
from image_translater import ImageTranslater

class MarkdonwAction(Enum):
    CRAWLER = 1
    JINA = 2
    MARKDOWNIFY = 3
class ImageAction(Enum):
    REPLACE = 1
    MARK = 2
class Translater():
    def __init__(self,url:str|list[str]|None=None,dictionaryFilename="dictionary.json",
                 taskFilename="task.json",crawlLevel=1,limit=10,markdownAction=MarkdonwAction.CRAWLER):
        self.markdownAction = markdownAction
        self.limit = limit
        self.crawlLevel = crawlLevel
        self.taskFilename = taskFilename
        self.imageTranslater = None
        self.config = Config()
        FileLib.mkdir("temp")
        if type(url)==list:
            self.url = url
            self.task = FileLib.loadJson(self.taskFilename)
            for url in self.url:
                id = HashLib.md5(url)
                if not self.task.get(id):
                    self.task[id] = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
            FileLib.dumpJson(self.taskFilename,self.task)
        elif url!=None:
            if self.crawlLevel==0:
                self.url = [url]
            else:
                self.url = list(self.getAllLinks(url))
            self.task = FileLib.loadJson(self.taskFilename)
            for url in self.url:
                id = HashLib.md5(url)
                if not self.task.get(id):
                    self.task[id] = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
            FileLib.dumpJson(self.taskFilename,self.task)
        else:
            self.task = FileLib.loadJson(self.taskFilename)
            self.url = list(map(lambda x:x["url"],self.task.values()))
        self.verify_args()
        self.dictionaryFilename = dictionaryFilename
        self.dict={}
        self.markdown_chain = self.getMarkdownChain()
        self.html_chain = self.getHTMLChain()
        self.setCrawl()
        self.dictionary = FileLib.loadJson(dictionaryFilename)

    def verify_args(self):
        assert True
           
    def getMarkdownChain(self):
        # llm = get_chatopenai_llm(
        #     base_url="https://api.together.xyz/v1",
        #     api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
        #     model="meta-llama/Llama-3-8b-chat-hf",
        #     temperature=0.2
        #     )
        llm = get_chatopenai_llm(
            base_url="https://api.together.xyz/v1",
            api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
            #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
            model="Qwen/Qwen1.5-72B-Chat",temperature=0)
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请将下面的markdown格式文档全部翻译成中文。
        注意:
          1、不要有遗漏,简单明了。
          2、特别不要遗漏嵌套的mardkown的语法
          3、禁止翻译代码中的JSON的key
          4、保留所有空白行,以确保markdown格式正确
          5、检查翻译的结果,以确保语句通顺
        \n\n"""
        prompt = get_prompt(textwrap.dedent(systemPromptText))
        chain = prompt | llm
        return chain
    def getHTMLChain(self):
        # llm = get_chatopenai_llm(
        #     base_url="https://api.together.xyz/v1",
        #     api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
        #     model="meta-llama/Llama-3-8b-chat-hf",
        #     temperature=0.2
        #     )
        llm = get_chatopenai_llm(
            base_url="https://api.together.xyz/v1",
            api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
            model="Qwen/Qwen1.5-72B-Chat",temperature=0)
        # llm = get_chatopenai_llm(
        #     api_key= self.config.get("LLM",{}).get("SILICONFLOW_API_KEY"),
        #     base_url="https://api.siliconflow.cn/v1",
        #     #model="alibaba/Qwen2-57B-A14B-Instruct",
        #     model="alibaba/Qwen1.5-110B-Chat",
        #     temperature=0)
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务及技术接口,擅长这些方面的技术文档的翻译。
    现在请将下面的HTML格式的英文文本全部翻译成中文,输出HTML文档,不要做任何解释。输出格式为```html ...```
    要求:
        1、尽量理解标签结构及上下文，该翻译的尽量翻译，不要有遗漏,简单明了
        2、禁止翻译代码中的非注释内容
        3、表格中全部大写字母的为错误代码，禁止翻译
        4、保持所有原始的HTML格式及结构
        5、检查翻译的结果,以确保语句通顺
    """
        prompt = get_prompt(textwrap.dedent(systemPromptText))
        chain = prompt | llm
        return chain
    def setCrawl(self):
        crawler = FirecrawlApp(api_key='fc-623406fb9b904381bd106e25244b38f5')
        self.crawler = crawler
        return crawler
    def clearErrorMsg(self):
        for id,taskItem in self.task.items():
            if taskItem.get("errorMsg") and taskItem.get("errorMsg")!="":
                taskItem["errorMsg"] = ""
        FileLib.dumpJson(self.taskFilename,self.task)
    def getLinks(self,url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到所有的a标签，这些通常代表链接
        links = [a['href'] for a in soup.find_all('a', href=True)]
        # 去除相对路径，转换为绝对路径
        links = [urljoin(url,link) for link in set(links)]
        return links
    def getAllLinks(self,url, visited=None,level=0):        
        if visited is None:
            visited = set()
        visited.add(url)
        # 发送GET请求
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 找到所有的a标签，这些通常代表链接
        links = [a['href'] for a in soup.find_all('a', href=True)]
        # 去除相对路径，转换为绝对路径
        links = [urljoin(url, link) for link in links]
        # 过滤不在同一域名下的链接和已访问过的链接
        links = [link for link in links if urlparse(link).netloc == urlparse(url).netloc and link not in visited]
        # 递归获取所有链接
        level += 1
        if level <= self.crawlLevel:
            for link in links:
                visited.add(link)
                #if len(visited) >= self.limit:
                #    break
                self.getAllLinks(link, visited, level=level)
        return visited
    def forceTableMarkdown(self,match):
        return markdownify(match.group())
    def getMarkdown(self,url):
        if self.markdownAction==MarkdonwAction.JINA:
            try:
                tokens = ["jina_93597c2c9a664e9791b029db95d526d9T8xm11r0PuQX0Rs2rqb7tMrMu4XA"]
                token = random.choice(tokens)
                res = requests.get(f"https://r.jina.ai/{url}",
                                   headers={"Accept":"application/json",
                                            "X-Return-Format":"markdown",
                                            #"Authorization": f"Bearer {token}"
                                            })
                # res = requests.get(f"https://r.jina.ai/{url}",
                #                 headers={"Accept":"application/json",
                #                             "X-Return-Format":"markdown"})
                #强制table转换
                FileLib.writeFile("current0.md",json.loads(res.text)['data']['content'])
                forcedMarkdown = re.sub( r"<table.*>.+</table>",self.forceTableMarkdown,json.loads(res.text)['data']['content'])
                FileLib.writeFile("current1.md",forcedMarkdown)
                content = {"content": forcedMarkdown}
            except Exception as e:
                raise Exception(f"[error on getMarkdown]: {json.loads(res.text) if res else str(e)}")     
            return content
        elif self.markdownAction==MarkdonwAction.MARKDOWNIFY:
            res = requests.get(f"{url}")
            return {"html":res.text,"content":markdownify(res.text)}
        else:  #None or MarkdownAction.CRAWLER
            params = {
                  "pageOptions":{
                    "includeHtml": True
                  }
                }
            res = self.crawler.scrape_url(url,params=params)
            return res

    def start(self):
        pass
class MarkdownTranslater(Translater):
    # translater = MarkdownTranslater(url= url,crawlLevel=1,markdownAction=MarkdonwAction.JINA)
    # translater.start()
    # url为None，则根据self.taskFilename的任务执行
    # url为单个网址，则根据crawlLevel的层级获取url。其中为0表示当前网址，为1表示当前网页的一级链接，以此类推
    # url为网址数组，则忽略crawlLevel，与self.taskFilename的网址合并任务
    def translate_markdown_text(self,chain,text):
        splits = split_markdown_docs(text)
        blocks = list(map(lambda block:block.page_content,splits))
        newBlocks = []
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                FileLib.writeFile(f"part_{index}.md",block)
                try:
                    #writeFile(f"block_{index}.md",block)
                    if self.dictionary.get(block):
                        return self.dictionary[block]
                    result = chain.invoke(
                        {
                            "input": block,
                        }
                    )
                    content = result.content
                    self.dictionary[text]=content
                    FileLib.writeFile(f"part_{index}_cn.md",content)
                    newBlocks.append(content)
                    pbar.update(1)
                except Exception as e:
                    print(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                    raise e
        return "\n\n".join(newBlocks)
    def start(self, imageAction:ImageAction|None=None):
        total = len(self.url)
        logger.info(f"begin on {total} urls\n")
        startTime = time.time()
        for index,url in enumerate(self.url):
            try:
                id = HashLib.md5(url)
                taskItem = self.task.get(id)
                if not taskItem:
                    taskItem = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
                    self.task[id] = taskItem
                if taskItem.get('errorMsg'):
                    logger.error(f"skip on url={url},id={id} ,because it is error ")
                    continue
                if not os.path.exists(f"{id}.md"):
                    logger.info(f"提取markdown url= {url},id={id} ...")
                    response = self.getMarkdown(url)
                    originHtml = response.get("html",None)
                    originMarkdown = response.get("content",None)
                    metadata = response.get("metadata",None)
                    if originMarkdown:
                        FileLib.writeFile(f"{id}.md",originMarkdown)
                        image_links = re.findall(r"!\[(.*?)\]\((.*?)\)",originMarkdown)
                        taskItem["imageLinks"] = list(map(lambda item:[item[0],item[1],HashLib.md5(item[1])],image_links))
                    if originHtml:
                        FileLib.writeFile(f"{id}.html",originHtml)
                    if metadata:
                        taskItem["metadata"] = metadata
                    taskItem["markdownAction"] = str(self.markdownAction)
                else:
                    originMarkdown = FileLib.readFile(f"{id}.md")
                resultMarkdown = None
                if not os.path.exists(f"{id}_cn.md"):
                    logger.info(f"开始翻译 url= {url},id={id} ...")
                    resultMarkdown = self.translate_markdown_text(self.markdown_chain,originMarkdown)
                    FileLib.writeFile(f"{id}_cn.md",resultMarkdown)
                else:
                    resultMarkdown = FileLib.readFile(f"{id}_cn.md")
                if resultMarkdown and imageAction:
                    if not self.imageTranslater:
                        self.imageTranslater = ImageTranslater()
                    if imageAction==ImageAction.REPLACE:
                        with tqdm(total= len(taskItem["imageLinks"])) as pbar: 
                            for imageLink in taskItem["imageLinks"]:
                                self.imageTranslater.start(imageLink[1],mode="replace")
                                resultMarkdown = self.replace_img_link(imageLink[1],resultMarkdown)
                                pbar.update(1)
                    elif imageAction==ImageAction.MARK:
                        with tqdm(total= len(taskItem["imageLinks"])) as pbar: 
                            for imageLink in taskItem["imageLinks"]:
                                self.imageTranslater.start(imageLink[1],mode="mark")
                                resultMarkdown = self.replace_img_link(imageLink[1],resultMarkdown)
                                pbar.update(1)
                    FileLib.writeFile(f"{id}_cn.md",resultMarkdown)
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                taskItem["errorMsg"] = str(e)
                logger.error(f"error on url={url},id={id},error={str(e)}")
                #raise e
        FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        FileLib.dumpJson(self.taskFilename,self.task)
        if imageAction and self.imageTranslater:
            self.imageTranslater.save()
    def replace_img_link(self,url,text):
        # 正则表达式模式，匹配 Markdown 图片语法 ![alt_text](image_url)
        pattern = re.compile(r'!\[([^\]]*)\]\(' + re.escape(url) + r'\)')
        # 使用新的链接替换所有旧的链接
        imageId = HashLib.md5(url)
        imageTask = self.imageTranslater.get_task_by_id(imageId)
        if imageTask:
            if imageTask['mode']=='replace':
                imageMode = 'r'
            else:
                imageMode = 'm'
            imageType = imageTask['imageType']
            result = text
            if imageType and imageType=='svg':
                newImageLink = f"./img_{imageMode}_{imageId}.{imageType}"
                result = pattern.sub(r'![\1](' + newImageLink + r')', text)
        return result
    def fix_markdown_script(self,markdown):
        pattern = re.compiler(r'copy\n(.*)X{512}')
        return pattern.sub(pattern,markdown)
    def fix_markdown_table(self,markdown):
        pass                      
class HTMLTranslater(Translater):
    def update_dictionary(self, origin_soup, target_soup):
        if SoupLib.compare_soup_structure(origin_soup,target_soup):
            origin_texts = SoupLib.find_all_text(origin_soup)
            target_texts = SoupLib.find_all_text(target_soup)
            if len(origin_texts) == len(target_texts):
                soup_dict = dict(zip(origin_texts,target_texts))
                self.dictionary = {**soup_dict, **self.dictionary}
    def translate_html_text(self,url_id,chain,text,size=1000):
        if FileLib.existsFile(f"temp/{url_id}/soup.html"):
            html = FileLib.readFile(f"temp/{url_id}/soup.html")
            soup = SoupLib.html2soup(html)
            hash_dict = FileLib.loadJson(f"temp/{url_id}/hash_dict.json")
            blocks = FileLib.readFiles(f"temp/{url_id}","part_[0-9]*.html")
            newBlocks = []       
        else:
            soup = SoupLib.html2soup(text)
            soup = SoupLib.add_tag(soup,"ignore",['//section[contains(@class,"right")]','//aside'])
            hash_dict = SoupLib.hash_attribute(soup)
            blocks = []
            newBlocks = []
            SoupLib.walk(soup, size=size,blocks=blocks,ignore_tags=["script", "style", "ignore","svg"])
            FileLib.writeFile(f"temp/{url_id}/soup.html",SoupLib.soup2html(soup))
            FileLib.dumpJson(f"temp/{url_id}/hash_dict.json",hash_dict)
            for idx,block in enumerate(blocks):
                FileLib.writeFile(f"temp/{url_id}/part_{str(idx).zfill(3)}.html",block)
                
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                if FileLib.existsFile(f"temp/{url_id}/part_{str(index).zfill(3)}_cn.html"):
                    content = FileLib.readFile(f"temp/{url_id}/part_{str(index).zfill(3)}_cn.html")
                    newBlocks.append(content)
                    pbar.update(1)
                else:
                    try:
                        soup_block = SoupLib.html2soup(block)
                        if SoupLib.find_all_text(soup_block):
                            SoupLib.replace_text_with_dictionary(soup_block,self.dictionary)
                            block_replaced = SoupLib.soup2html(soup_block)
                            result = chain.invoke(
                                {
                                    "input": block_replaced,
                                }
                            )
                            content = result.content
                            self.update_dictionary(soup_block,SoupLib.html2soup(content))
                            FileLib.writeFile(f"temp/{url_id}/part_{str(index).zfill(3)}_cn.html",content)
                            newBlocks.append(content)
                        else:
                            newBlocks.append(block)
                        pbar.update(1)
                    except Exception as e:
                        print(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                        #raise e
        SoupLib.unwalk(soup,newBlocks)
        SoupLib.unhash_attribute(soup,hash_dict)
        soup = SoupLib.remove_tag(soup,"ignore")
        resultHtml = soup.prettify("utf-8")
        return resultHtml.decode("utf-8")
    async def get_html(self, url):
        async with PlaywrightLib(headless=False) as pw:
            await pw.goto(url,start_log="开始加载页面",end_log="页面加载完成",wait_until="domcontentloaded",timeout=180000)
            pw.wait(3000,start_log="等待3秒",end_log="等待结束")
            print(await pw.selector_exists('//section[contains(@class,"right")]'))
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
        logger.info(f"begin on {total} urls\n")
        startTime = time.time()
        for index,url in enumerate(self.url):
            try:
                id = HashLib.md5(url)
                FileLib.mkdir(f"temp/{id}")
                taskItem = self.task.get(id)
                if not taskItem:
                    taskItem = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
                    self.task[id] = taskItem
                if taskItem.get('errorMsg'):
                    logger.error(f"skip on url={url},id={id} ,because it is error ")
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
                        resultHtml = self.translate_html_text(id,self.html_chain,originHtml,size=size)
                        FileLib.writeFile(f"{id}_cn.html",resultHtml)
                    else:
                        resultHtml = FileLib.readFile(f"{id}_cn.html")
                
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                taskItem["errorMsg"] = str(e)
                logger.error(f"error on url={url},id={id},error={str(e)}")
                #raise e
        FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        FileLib.dumpJson(self.taskFilename,self.task)
        if imageAction and self.imageTranslater:
            self.imageTranslater.save()       

async def main():
    logger.setLevel(logging.INFO)
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    crawlLevel = 0
    if len(sys.argv) > 2:
        crawlLevel = int(sys.argv[2])
    '''url = ["https://global.alipay.com/docs/",
    "https://global.alipay.com/docs/ac/flexiblesettlement_en/overview",
    "https://global.alipay.com/docs/ac/scantopay_en/overview",
    "https://global.alipay.com/docs/ac/cashierpay/apm_ww",
    "https://global.alipay.com/docs/ac/scan_to_bind_en/refund",
    "https://global.alipay.com/docs/ac/cashierpay/apm_api",
    "https://global.alipay.com/docs/ac/cashierpay/prefront"
    ]'''
    #url = "https://global.alipay.com/docs/ac/subscriptionpay_en/overview"
    #url = "https://global.alipay.com/docs/ac/cashierpay/apm_api"
    #url = "https://global.alipay.com/docs/ac/cashierpay/overview" #有中文
    #url = "https://global.alipay.com/docs/ac/reconcile/settlement_details"
    if not url:
        #url = "https://global.alipay.com/docs"
        #url = "https://global.alipay.com/docs/ac/cashierpay/overview"
        #url = "https://global.alipay.com/docs/ac/easypay_en/overview_en"
        #url = "https://global.alipay.com/docs/ac/scantopay_en/overview"
        #url = "https://global.alipay.com/docs/ac/autodebit_en/overview"
        #url = "https://global.alipay.com/docs/ac/subscriptionpay_en/overview"
        #url = "https://global.alipay.com/docs/instorepayment"
        #url = "https://global.alipay.com/docs/ac/cashierpay/apm_android"
        #url = "https://global.alipay.com/docs/ac/subscriptionpay_en/activation"
        #url = "https://global.alipay.com/docs/ac/cashierpay/urls" #有问题
        #url = "https://global.alipay.com/docs/ac/ref/sandbox"
        #url = "https://huggingface.co/davidkim205/Rhea-72b-v0.5/discussions"
        #url = "https://global.alipay.com/docs/ac/subscriptionpay_en/overview"
        url = "https://global.alipay.com/docs/ac/ams/api"
    urls = ["https://global.alipay.com/docs/ac/ams/authconsult",
            "https://global.alipay.com/docs/ac/ams/notifyauth",
            "https://global.alipay.com/docs/ac/ams/accesstokenapp",
            "https://global.alipay.com/docs/ac/ams/authrevocation",
            "https://global.alipay.com/docs/ac/ams/vaulting_session",
            "https://global.alipay.com/docs/ac/ams/vault_method",
            "https://global.alipay.com/docs/ac/ams/notify_vaulting",
            "https://global.alipay.com/docs/ac/ams/inquire_vaulting",
            "https://global.alipay.com/docs/ac/ams/consult",
            "https://global.alipay.com/docs/ac/ams/payment_cashier",
            "https://global.alipay.com/docs/ac/ams/session_cashier",
            "https://global.alipay.com/docs/ac/ams/capture",
            "https://global.alipay.com/docs/ac/ams/payment_agreement",
            "https://global.alipay.com/docs/ac/ams/createpaymentsession_easypay",
            "https://global.alipay.com/docs/ac/ams/paymentrn_online",
            "https://global.alipay.com/docs/ac/ams/notify_capture",
            "https://global.alipay.com/docs/ac/ams/paymentri_online",
            "https://global.alipay.com/docs/ac/ams/paymentc_online",
            "https://global.alipay.com/docs/ac/ams/create_sub",
            "https://global.alipay.com/docs/ac/ams/notify_sub",
            "https://global.alipay.com/docs/ac/ams/notify_subpayment",
            "https://global.alipay.com/docs/ac/ams/change_sub",
            "https://global.alipay.com/docs/ac/ams/cancel_sub",
            "https://global.alipay.com/docs/ac/ams/accept",
            "https://global.alipay.com/docs/ac/ams/supply_evidence",
            "https://global.alipay.com/docs/ac/ams/download",
            "https://global.alipay.com/docs/ac/ams/notify_dispute",
            "https://global.alipay.com/docs/ac/ams/refund_online",
            "https://global.alipay.com/docs/ac/ams/notify_refund",
            "https://global.alipay.com/docs/ac/ams/ir_online",
            "https://global.alipay.com/docs/ac/ams/declare",
            "https://global.alipay.com/docs/ac/ams/inquirydeclare"
            ]
    ###### markdown模式
    # translater = MarkdownTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.JINA)
    # translater.clearErrorMsg()
    # translater.start(imageAction=ImageAction.MARK)
    # #translater.start()

    # ###### html模式
    translater = HTMLTranslater(url=urls,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.CRAWLER)
    #translater.clearErrorMsg()
    await translater.start(size=2000)
    
    # ######  测试翻译html片段
    # print(1,translater.config.get("LLM",{}).get("SILICONFLOW_API_KEY"))
    # html = FileLib.readFile("part_13.html")
    # print(2,html)
    # res = translater.html_chain.invoke({"input":html})
    # print(res.content)
    #llm = ChatOpenAI(base_url="https://api.together.xyz/v1",api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",model="Qwen/Qwen1.5-72B-Chat")
    #llm.invoke("hello")
    ##### playwright
    '''
    async with PlaywrightLib(headless=False) as pw:
        await pw.goto(url,start_log="开始加载页面",end_log="页面加载完成",wait_until="domcontentloaded")
        pw.wait(3000,start_log="等待3秒",end_log="等待结束")
        print(await pw.selector_exists('//section[contains(@class,"right")]'))
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
        FileLib.writeFile("pw.html",html[0])
        pw.wait(10000,start_log="等待10秒",end_log="等待结束")
    
        await pw.close()
        html = [FileLib.readFile("pw.html")]
        soup = SoupLib.html2soup(html[0])
        hash_dict = SoupLib.hash_attribute(soup)
        blocks = []
        SoupLib.walk(soup, size=2000,blocks=blocks)
        print(len(blocks))
        for idx,item in enumerate(blocks):
            temp = SoupLib.html2soup(item)
            if temp.text:
                print(idx,len(item))
            #FileLib.writeFile(f"pw_{idx}.html",item)
    '''
    # html = FileLib.readFile("pw.html")
    # soup = SoupLib.html2soup(html)
    # soup = SoupLib.add_tag(soup,"ignore",['//section[contains(@class,"right")]'])
    # #soup2 = SoupLib.remove_tag(soup,"ignore")
    # hash_dict = SoupLib.hash_attribute(soup)
    # blocks = []
    # SoupLib.walk(soup, size=2000,blocks=blocks,ignore_tags= ["script", "style", "ignore","svg"])
    # #print("*"*20,soup,"*"*20)
    # print(len(blocks))
    # for idx,block in enumerate(blocks):
    #     print(idx,len(block),len(SoupLib.find_all_text(SoupLib.html2soup(block))))
    # print("*"*20,)
    # idx = 16
    # FileLib.writeFile(f"block{idx}.html",blocks[idx])
    # print(SoupLib.html2soup(blocks[idx]).get_text(separator='||', strip=True))
    # #content = translater.html_chain.invoke({"input":blocks[idx]}).content
    # print("*"*20)
    # #print(SoupLib.html2soup(content).get_text(separator='||', strip=True))
    # for i,item in enumerate(SoupLib.find_all_text(SoupLib.html2soup(blocks[idx]))):
    #     print(i,item)
    # dictionary = {"Array":"列表","is":"是"}
    # soup1 = SoupLib.html2soup(blocks[idx])
    # #soup1.contents[0].attrs={"t":"abcdef"}
    # soup2 = SoupLib.html2soup(blocks[idx])
    # SoupLib.replace_text_with_dictionary(soup2,dictionary)
    # print(soup1,"\n\n",soup2)
    # print(SoupLib.compare_soup_structure(soup1,soup2))
    # translater.update_dictionary(soup1,soup2)
    # print(translater.dictionary)

    #for idx,block in enumerate(blocks):
    #    FileLib.writeFile(f"pw_{idx}.html",block)

    '''
    #表格
    //div[@data-lake-card="table"]
    #代码段
    //div[@data-lake-card="codeblock"]
    #图片
    //span[@data-lake-card="image"]
    #右侧侧边导航
    //nav
    #左侧菜单导航
    //aside
    #主内容
    //article

    # 要翻译的部分
    //article[@class="ant-typography"]//section
    # sandboxSwitch span按钮
    //div[contains(@class,"sandboxSwitch")]//span[text()="Sample Codes"]
    //div[contains(@class,"sandboxSwitch")]//span[text()="Run in Sandbox"]
    #脚本文本
    //div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]
    #定位id
    //*[@id="3RxeL"]
    //*[@id="d8Mc5"]

    '''
    

if __name__ == "__main__":
   asyncio.run(main()) 