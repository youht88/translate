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
from logger import logger

import random

from translate.utils.config_utils import Config
from translate.utils.file_utils import FileLib
from translate.utils.crypto_utils import HashLib
from translate.utils.langchain_utils import *

from enum import Enum

#print("translate init....")
class MarkdonwAction(Enum):
    CRAWLER = 1
    JINA = 2
    MARKDOWNIFY = 3
class ImageAction(Enum):
    REPLACE = 1
    MARK = 2

class Translater():
    def __init__(self,url:str|list[str]|None=None,dictionaryFilename="dictionary.json",
                 taskFilename="task.json",crawlLevel=1,limit=10,markdownAction=MarkdonwAction.CRAWLER,env_file=None):
        self.markdownAction = markdownAction
        self.limit = limit
        self.crawlLevel = crawlLevel
        self.taskFilename = taskFilename
        self.imageTranslater = None
        self.config = Config('translate',env_file)
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
        self.setCrawl()
        self.dictionary = FileLib.loadJson(dictionaryFilename)

    def verify_args(self):
        assert True
    def get_chain(self):
        raise "must implement get_chain function"       
    def setCrawl(self):
        crawler = FirecrawlApp(api_key='fc-623406fb9b904381bd106e25244b38f5')
        self.crawler = crawler
        return crawler
    def clearErrorMsg(self):
        logger.info("!!!!清除task所有的错误标记!!!!")
        for id,taskItem in self.task.items():
            if taskItem.get("errorMsg",""):
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
