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

from utils.file_utils import FileLib
from utils.crypto_utils import HashLib
from utils.langchain_utils import *
from utils.soup_utils import SoupLib
from utils.config_utils import Config
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
    def snipHtml(self,tagObject,beforeNum=2,afterNum=2):
        print(str(tagObject.parent))
        parent = BeautifulSoup(str(tagObject.parent), "html.parser")
        previousAll = list(filter(lambda x:x!='\n',tagObject.previous_siblings))
        nextAll = list(filter(lambda x:x!='\n',tagObject.next_siblings))
        parent.clear()
        for i in range(beforeNum if beforeNum<len(previousAll) else len(previousAll)):
            parent.insert(0,previousAll[i])
        if beforeNum < len(previousAll):
            other = self.soup.new_tag('p')
            other.string = '...'
            parent.insert(0,other)
        parent.append(tagObject) 
        for i in range(afterNum if afterNum<len(nextAll) else len(nextAll)):
            parent.append(nextAll[i])
        if afterNum < len(nextAll):
            other = self.soup.new_tag('p')
            other.string = '...'
            parent.append(other)
        print(parent,'\n','*'*20,'\n',self.soup)
    def translate_html_text(self,chain,text):
        soup = SoupLib.html2soup(text)
        hash_dict = SoupLib.hash_attribute(soup)
        blocks = []
        newBlocks = []
        SoupLib.walk(soup, size=1000,blocks=blocks)
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                FileLib.writeFile(f"part_{index}.html",block)
                try:
                    if self.dictionary.get(block):
                        return self.dictionary[block]
                    result = chain.invoke(
                        {
                            "input": block,
                        }
                    )
                    content = result.content
                    self.dictionary[text]=content
                    FileLib.writeFile(f"part_{index}_cn.html",content)
                    newBlocks.append(content)
                    pbar.update(1)
                except Exception as e:
                    print(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                    raise e
        SoupLib.unwalk(soup,newBlocks)
        SoupLib.unhash_attribute(soup,hash_dict)
        resultHtml = soup.prettify("utf-8")
        return resultHtml.decode("utf-8")
    def start_old(self):
        # 翻译 HTML 中的文本，指定目标语言为中文
        for element in self.soup.find_all(text=True):
            if element.parent.name not in ["script", "style"]:
                tagSet = ("code","table")
                tagAction = "ignore" # "must"
                parentTag = map(lambda x:x.name,element.parents) # 跳过 script 和 style 标签内的文本
                if tagAction=="must" and (not set(tagSet).intersection(parentTag)):
                    continue
                if tagAction=="ignore" and set(tagSet).intersection(parentTag):
                    continue
                original_text = element.string
                translated_text = original_text
                if original_text!="\n":
                    translated_text = self.translate_text(original_text)
                    print(f"A:{repr(original_text)}\nB:{repr(translated_text)}\nC:{element}\nD:<{element.parent.name}>\nE:{repr(element.parent)}>\n{'*'*20}\n")
                    element.replace_with(translated_text)
        # 生成翻译后的 HTML
        translated = self.soup.prettify("utf-8")
        self.writeOrigin(self.html)
        self.writeTranslated(translated)
        self.writeDictionary() 
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
                if not os.path.exists(f"{id}.html"):
                    logger.info(f"提取html url= {url},id={id} ...")
                    response = requests.get(url)
                    originHtml = response.text
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
                if not os.path.exists(f"{id}_cn.html"):
                    logger.info(f"开始翻译 url= {url},id={id} ...")
                    resultHtml = self.translate_html_text(self.html_chain,originHtml)
                    FileLib.writeFile(f"{id}_cn.html",resultHtml)
                else:
                    resultHtml = FileLib.readFile(f"{id}_cn.html")
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                taskItem["errorMsg"] = str(e)
                logger.error(f"error on url={url},id={id},error={str(e)}")
                raise e
        FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        FileLib.dumpJson(self.taskFilename,self.task)
        if imageAction and self.imageTranslater:
            self.imageTranslater.save()       

if __name__ == "__main__":
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
    urls = ["https://global.alipay.com/docs/ac/subscriptionpay_en/overview",
            "https://global.alipay.com/docs/ac/subscriptionpay_en/activation?pageVersion=9",
            "https://global.alipay.com/docs/ac/subscriptionpay_en/cancel_refund",
            "https://global.alipay.com/docs/ac/subscriptionpay_en/reconcile"]
    ###### markdown模式
    # translater = MarkdownTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.JINA)
    # translater.clearErrorMsg()
    # translater.start(imageAction=ImageAction.MARK)
    # #translater.start()

    # ###### html模式
    translater = HTMLTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.CRAWLER)
    # #translater.clearErrorMsg()
    # translater.start()
    
    ######  测试翻译html片段
    print(1,translater.config.get("LLM",{}).get("SILICONFLOW_API_KEY"))
    html = FileLib.readFile("part_13.html")
    print(2,html)
    res = translater.html_chain.invoke({"input":html})
    print(res.content)
    '''
    表格
    //div[@data-lake-card="table"]
    代码段
    //div[@data-lake-card="codeblock"]
    图片
    //span[@data-lake-card="image"]
    右侧侧边导航
    //nav
    左侧菜单导航
    //aside
    主内容
    //article
    '''
    