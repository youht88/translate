from urllib.parse import urljoin, urlparse
import langchain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_core.documents import Document
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter
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
class Translater():
    def __init__(self,url:str|list[str],dictionaryFilename="dictionary.json",taskFilename="task.json",limit=10):
        self.limit = limit
        self.url = url if type(url)==list else [url]
        self.verify_args()
        self.dictionaryFilename = dictionaryFilename
        self.taskFilename = taskFilename
        self.dict={}
        self.task={}
        self.llm = None
        self.soup = None
        self.setLLM()
        self.setPrompt()
        self.setChain(self.llm, self.prompt)
        self.setCrawl()
        self.dictionary = self.loadJson(dictionaryFilename)
        self.task = self.loadJson(taskFilename)
        # 获取 HTML 网页
        #url = "https://global.alipay.com/docs/"
        #url = "https://global.alipay.com/docs/ac/ams_oc/introduction"
        #url = "https://global.alipay.com/docs/ac/cashierpay/apm_api" 
        #url = "https://global.alipay.com/docs/ac/easypay_en/overview_en"
        print(self.task)
    def verify_args(self):
        assert self.url != None
    
    def md5(self,string):
        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()
    def splitDocs(self,text,line=200,code=True,table=True):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on,strip_headers=False)
        docs = markdown_splitter.split_text(text)
        print("len(docs):",len(docs))
        print("docs.metata:",list(map(lambda doc:doc.metadata,docs)))
        return list(map(lambda doc:doc.page_content,docs))
    def translate_text(self,text):
        blocks = self.splitDocs(text,line=200,code=True,table=True)
        newBlocks = []
        #with tqmd(total= len(blocks)) as pbar:
        for index,block in enumerate(blocks):
            if self.dictionary.get(block):
                return self.dictionary[block]
            result = self.chain.invoke(
                {
                    "input": block,
                }
            )
            content = result.content
            self.dictionary[text]=content
            newBlocks.append(content)
            #pbar.update(1)
        return "\n".join(newBlocks)
    def setLLM(self):
        chat_llama3 = ChatOpenAI(
            base_url="https://api.together.xyz/v1",
            api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
            #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
            model="meta-llama/Llama-3-8b-chat-hf",)
        chat_qwen72b = ChatOpenAI(
            base_url="https://api.together.xyz/v1",
            api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
            #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
            model="Qwen/Qwen1.5-72B-Chat",)
        self.llm = chat_qwen72b
    def setChain(self,llm,prompt):
        chain = prompt | llm
        self.chain = chain
        return chain
    def setCrawl(self):
        crawler = FirecrawlApp(api_key='fc-623406fb9b904381bd106e25244b38f5')
        self.crawler = crawler
        return crawler
    def loadJson(self,filename):
        try:
            with open(filename,"r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"{filename} error.",e)
            data = {}
        return data
    def dumpJson(self,filename,data):
        try:
            with open(filename,"w") as f:
                json.dump(data,f)
        except Exception as e:
            print(f"{filename} error.",e)

    
    def writeFile(self,filename,text):
        # 保存文件
        with open(filename, "w") as f:
            f.write(text)        
            print(f"File saved to {filename}")
    def readFile(self,filename):
        with open(filename,"r") as f:
            text = f.read()
        return text
    def setPrompt(self):
        systemPromptText = """尽你的最大可能和能力回答用户问题。不要重复回答问题。不要说车轱辘话。语言要通顺流畅。不要出现刚说一句话，过一会又重复一遍的愚蠢行为。
          RULES:
          1. Beprecise,do not reply emoji or other non-sense.
          2. Always response in Simplified Chinese,not English. or Granama will be very angry.
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
    def getLinks(self,url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到所有的a标签，这些通常代表链接
        links = [a['href'] for a in soup.find_all('a', href=True)]
        # 去除相对路径，转换为绝对路径
        links = [urljoin(url,link) for link in set(links)]
        return links
    def getAllLinks(self,url, visited=None):
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
        for link in links:
            visited.add(link)
            if len(visited) >= self.limit:
                break
            self.getAllLinks(link, visited)
        return visited
    def start(self):
        pass
class MarkdownTranslater(Translater):
    def setPrompt(self):
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请将下面的markdown格式文档全部翻译成中文。
        注意:
          1、不要有遗漏
          2、简单明了
        \n\n"""
        # systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务，擅长将这些方面的技术文档的翻译。请将以下Markdown文字翻译成中文。
        #   要求
        #   1.简单明了
        #   2.碰到专有名词、代码、数字、url、程序接口、程序方法名称以及缩写的情况直接输出原始内容
        #   3.如果不需要翻译则直接输出原始内容。例如: 输入 XXX , 输出 XXX
        #   4.任何情况下不要解释原因。
        # """
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
    def start(self):
        total = len(self.url)
        for index,url in enumerate(self.url):
            id = self.md5(url)
            taskItem = self.task.get(id)
            if not taskItem:
                taskItem = {
                    "url": url,
                    "metadata": None,
                    "done": False
                }
                self.task[id] = taskItem
            if not os.path.exists(f"{id}.md"):
                params = {
                  "pageOptions":{
                    "includeHtml": True
                  }
                }
                response = self.crawler.scrape_url(url,params=params)
                originHtml = response["html"]
                originMarkdown = response["content"]
                metadata = response["metadata"]
                self.writeFile(f"{id}.md",originMarkdown)
                self.writeFile(f"{id}.html",originHtml)
                taskItem["metadata"] = metadata
            else:
                originMarkdown = self.readFile(f"{id}.md")
            if not os.path.exists(f"{id}_cn.md"):
                resultMarkdown = self.translate_text(originMarkdown)
                self.writeFile(f"{id}_cn.md",resultMarkdown)
                taskItem["done"] = True
            print(f"[{(index+1)/total*100}%]===>url->{url},id->{id}")
        self.dumpJson(self.dictionaryFilename,self.dictionary)
        self.dumpJson(self.taskFilename,self.task)
        
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
    def toMarkdown(self,html):
        return html2markdown.convert(html)
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
    url = ["https://global.alipay.com/docs/",
    "https://global.alipay.com/docs/ac/flexiblesettlement_en/overview",
    "https://global.alipay.com/docs/ac/scantopay_en/overview",
    "https://global.alipay.com/docs/ac/cashierpay/apm_ww",
    "https://global.alipay.com/docs/ac/scan_to_bind_en/refund",
    "https://global.alipay.com/docs/ac/cashierpay/apm_api",
    "https://global.alipay.com/docs/ac/cashierpay/prefront"
    ]
    #with open("origin.html","r") as f:
    #    html = f.read()
    #translater = HTMLTranslater(url=url)
    # translater = HTMLTranslater(html=html,dictFilename="/Users/youht/source/python/translate/translate/dict.json")
    # obj = translater.soup.select(".div1 .h2-1")
    # translater.snipHtml(obj[0])
    # translater.start()
    
    #translater = MarkdownTranslater(url = "https://global.alipay.com/docs")
    #translater = MarkdownTranslater(originFilename= "origin.md")
    
    translater = MarkdownTranslater(url= url)
    translater.start()
    #links = translater.getAllLinks(url)
    #print(len(links),links)
    #translater.start()
    
    # documents = [Document(page_content = str(translater.soup))]
    # print(documents)
    # html2text = Html2TextTransformer()
    # docs_transformed = html2text.transform_documents(documents)
    # print(docs_transformed)