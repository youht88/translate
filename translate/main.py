import time
from urllib.parse import quote, urljoin, urlparse
from markdownify import markdownify
import langchain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_core.documents import Document
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
from bs4 import BeautifulSoup
import re 
import json
from langchain_openai import ChatOpenAI
import copy
import hashlib
import os
from tqdm import tqdm

# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp
from enum import Enum
import random

import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image,ImageFont,ImageDraw
from IPython.display import HTML, display
import base64
from io import BytesIO
from logger import logger

from utils import *
from langchain_utils import *

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
        if type(url)==list:
            self.url = url
            self.task = loadJson(self.taskFilename)
            for url in self.url:
                id = self.md5(url)
                if not self.task.get(id):
                    self.task[id] = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
            dumpJson(self.taskFilename,self.task)
        elif url!=None:
            self.url = list(self.getAllLinks(url))
            self.task = loadJson(self.taskFilename)
            for url in self.url:
                id = md5(url)
                if not self.task.get(id):
                    self.task[id] = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
            dumpJson(self.taskFilename,self.task)
        else:
            self.task = loadJson(self.taskFilename)
            self.url = list(map(lambda x:x["url"],self.task.values()))
        self.verify_args()
        self.dictionaryFilename = dictionaryFilename
        self.dict={}
        self.markdown_chain = self.getMarkdownChain()
        self.llava_chain = self.getLlavaChain()
        self.setCrawl()
        self.dictionary = loadJson(dictionaryFilename)

    def verify_args(self):
        assert True
           
    def translate_markdown_text(self,chain,text):
        splits = split_markdown_docs(text)
        blocks = list(map(lambda block:block.page_content,splits))
        newBlocks = []
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
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
                    newBlocks.append(content)
                    pbar.update(1)
                except Exception as e:
                    print(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                    raise e
        return "\n".join(newBlocks)
    def getMarkdownChain(self):
        # llm = get_chatopenai_llm(
        #     base_url="https://api.together.xyz/v1",
        #     api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
        #     #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
        #     model="meta-llama/Llama-3-8b-chat-hf",
        #     temperature=0.2
        #     )
        llm = ChatOpenAI(
            base_url="https://api.together.xyz/v1",
            api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
            #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
            model="Qwen/Qwen1.5-72B-Chat",temperature=0.2)
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请将下面的markdown格式文档全部翻译成中文。
        注意:
          1、不要有遗漏
          2、简单明了
        \n\n"""
        prompt = get_prompt(systemPromptText)
        chain = prompt | llm
        return chain
    def getLlavaChain(self):
        pass
    def setCrawl(self):
        crawler = FirecrawlApp(api_key='fc-623406fb9b904381bd106e25244b38f5')
        self.crawler = crawler
        return crawler
    def clearErrorMsg(self):
        for id,taskItem in self.task.items():
            if taskItem.get("errorMsg") and taskItem.get("errorMsg")!="":
                taskItem["errorMsg"] = ""
        dumpJson(self.taskFilename,self.task)
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
                forcedMarkdown = re.sub( r"<table.*>.+</table>",self.forceTableMarkdown,json.loads(res.text)['data']['content'])
                content = {"content": forcedMarkdown}
            except Exception as e:
                raise Exception(f"[error on getMarkdown]: {json.loads(res.text)}")       
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
    def start(self, imageAction:ImageAction|None=None):
        total = len(self.url)
        logger.info(f"begin on {total} urls\n")
        startTime = time.time()
        for index,url in enumerate(self.url):
            try:
                id = md5(url)
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
                        writeFile(f"{id}.md",originMarkdown)
                        image_links = re.findall(r"!\[(.*?)\]\((.*?)\)",originMarkdown)
                        taskItem["imageLinks"] = list(map(lambda item:[item[0],item[1],md5(item[1])],image_links))
                    if originHtml:
                        writeFile(f"{id}.html",originHtml)
                    if metadata:
                        taskItem["metadata"] = metadata
                    taskItem["markdownAction"] = str(self.markdownAction)
                else:
                    originMarkdown = readFile(f"{id}.md")
                if not os.path.exists(f"{id}_cn.md"):
                    logger.info(f"开始翻译 url= {url},id={id} ...")
                    resultMarkdown = self.translate_markdown_text(self.markdown_chain,originMarkdown)
                    writeFile(f"{id}_cn.md",resultMarkdown)
                if imageAction:
                    if not self.imageTranslater:
                        self.imageTranslater = ImageTranslater()
                    if imageAction==ImageAction.REPLACE:
                        with tqdm(total= len(taskItem["imageLinks"])) as pbar: 
                            for imageLink in taskItem["imageLinks"]:
                                self.imageTranslater.start(imageLink[1],mode="replace")
                                pbar.update(1)
                    elif imageAction==ImageAction.MARK:
                        with tqdm(total= len(taskItem["imageLinks"])) as pbar: 
                            for imageLink in taskItem["imageLinks"]:
                                self.imageTranslater.start(imageLink[1],mode="mark")
                                pbar.update(1)
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                taskItem["errorMsg"] = str(e)
                logger.error(f"error on url={url},id={id}",e)
        dumpJson(self.dictionaryFilename,self.dictionary)
        dumpJson(self.taskFilename,self.task)
        self.imageTranslater.save()

class HTMLTranslater(Translater):
    # def __init__(self,url:str|list[str],dictionaryFilename="dictionary.json",taskFilename="task.json"):
    #     super().__init__(url,dictionaryFilename,taskFilename)
    #     if (self.url):
    #         self.originFilename="origin.html"
    #         response = requests.get(self.url)
    #         self.html = response.text
    #     else:
    #         with open(originFilename,"r",encoding="utf8") as f:
    #             self.html = f.read()
    #     # 解析 HTML
    #     self.soup = BeautifulSoup(self.html, "html.parser")
    def setPrompt(self):
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务，擅长将这些方面的技术文档的翻译。请将以下文字翻译成中文。
          要求
          1.简单明了
          2.碰到专有名词、代码、数字、url、程序接口、程序方法名称以及缩写的情况直接输出原始内容
          3.如果不需要翻译则直接输出原始内容。例如: 输入 XXX , 输出 XXX
          4.任何情况下不要解释原因。
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                
                (
                    "system",
                    systemPromptText,
                ),
                ("human", "{input}"),
            ]
        )
        self.prompt = prompt
        return prompt
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
    def start(self):
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
if __name__ == "__main__":
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

    #url = "https://global.alipay.com/docs"
    #url = "https://global.alipay.com/docs/ac/cashierpay/overview"
    #url = "https://global.alipay.com/docs/ac/easypay_en/overview_en"
    #url = "https://global.alipay.com/docs/ac/scantopay_en/overview"
    #url = "https://global.alipay.com/docs/ac/autodebit_en/overview"
    #url = "https://global.alipay.com/docs/ac/subscriptionpay_en/overview"
    #url = "https://global.alipay.com/docs/instorepayment"
    url = "https://global.alipay.com/docs/ac/cashierpay/apm_android"

    translater = MarkdownTranslater(url=url,crawlLevel=0, markdownAction=MarkdonwAction.JINA)
    translater.clearErrorMsg()
    translater.start(imageAction=ImageAction.MARK)
    