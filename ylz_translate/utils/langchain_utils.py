import logging
import inspect
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_community.llms import Ollama
from langchain_core.messages import SystemMessage,HumanMessage
from langchain_core.output_parsers import StrOutputParser

from langchain.memory import ConversationBufferMemory

from langchain.docstore.document import Document

from langchain_core.prompts import ChatPromptTemplate,PromptTemplate,SystemMessagePromptTemplate
from langchain_core.prompt_values import StringPromptValue,ChatPromptValue
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from markdownify import markdownify as MarkdownifyTransformer

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceBgeEmbeddings,
)
from langchain_together import TogetherEmbeddings

from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from operator import itemgetter

from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain.output_parsers import RetryOutputParser

from langchain_core.pydantic_v1 import BaseModel, Field, validator
from typing import List,Literal

from gradio_client import Client,file
import re

from .config_utils import Config
from .file_utils import FileLib
from .data_utils import Color, StringLib

import textwrap
import random
import time
from datetime import datetime

class LangchainLib():
    llms:list = []
    embeddings:list  = []
    def __init__(self):
        self.config = Config.get()
        self.add_plugins()
        self.regist_llm()
        self.regist_embedding()
        # 创建一个对话历史管理器
        self.memory = ConversationBufferMemory()

    def add_plugins(self):
        plugins = {"invoke":ChatOpenAI.invoke,
                   "ainvoke":ChatOpenAI.ainvoke,
                   "stream":ChatOpenAI.stream,
                   "astream":ChatOpenAI.astream,
            }
        def get_wrapper(func):
            logging.info(f"增加ChatOpenAI.{func.__name__}的插件!!")
            def sync_wrapper(self, *args,**kwargs):
                if isinstance(args[0],StringPromptValue):
                    text = args[0].text
                    args[0].text = f"现在是北京时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}\n{text}"
                elif isinstance(args[0],ChatPromptValue):
                    chatPromptValue = args[0]
                    chatPromptValue.messages.insert(0,SystemMessage(f"现在是北京时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"))
                return func(self, *args, **kwargs)
            async def async_wrapper(self, *args,**kwargs):
                if isinstance(args[0],StringPromptValue):
                    text = args[0].text
                    args[0].text = f"现在是北京时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}\n{text}"
                elif isinstance(args[0],ChatPromptValue):
                    chatPromptValue = args[0]
                    chatPromptValue.messages.insert(0,SystemMessage(f"现在是北京时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"))
                return await func(self, *args, **kwargs)
            if  inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        for key in plugins:
            func = plugins[key]
            setattr(ChatOpenAI,key,get_wrapper(func))

    def get_llm(self,key=None, full=False,delay=10)->ChatOpenAI:
        if self.llms:
            if not key:
                llms = self.llms
            else:
                if key == "LLM.GEMINI":
                    #macos不支持
                    llms=[]
                else:
                    llms = [item for item in self.llms if item['type']==key]
            if llms:
                while True:
                    llm = random.choice(llms) 
                    #print(llm.get('last_used',0),time.time() - llm.get('last_used'),llm['api_key'])   
                    over_delay = (time.time() - llm.get('last_used',0)) > delay # 3秒内不重复使用
                    if not over_delay:
                        continue
                    if not llm.get('llm'):
                        llm_type = llm.get('type')
                        if llm_type == 'LLM.GEMINI':
                            StringLib.logging_in_box(f"google_api_key={llm.get('api_key')},model={llm.get('model')}")
                            llm['llm'] = ChatGoogleGenerativeAI(
                                google_api_key=llm.get('api_key'), 
                                model=llm.get('model'),
                                temperature= llm.get('temperature'))
                        else:
                            llm['llm'] = ChatOpenAI(
                                base_url=llm.get('base_url'),
                                api_key= llm.get('api_key'),
                                model= llm.get('model'),
                                temperature= llm.get('temperature')
                                )
                    llm['used'] = llm.get('used',0) + 1 
                    llm['last_used'] = time.time()
                    if full:
                        return llm
                    else:
                        return llm['llm'] 
        raise Exception("请先调用regist_llm注册语言模型")
    
    def regist_llm(self):
        defaults = {"LLM.TOGETHER":
                      {"model":"Qwen/Qwen1.5-72B-Chat","temperature":0},
                   "LLM.SILICONFLOW":
                      {"model":"alibaba/Qwen1.5-110B-Chat","temperature":0},
                   "LLM.GROQ":
                      {"model":"llama3-70b-8192","temperature":0},
                   "LLM.GEMINI":
                      {"model":"gemini-pro","temperature":0}
                  }
        for key in defaults:
            default = defaults[key]
            language = self.config.get(key)
            base_url = language.get("BASE_URL")
            api_keys = language.get("API_KEYS")
            if api_keys:
                api_keys = api_keys.split(",")
            else:
                api_keys = []
            model= language.get("MODEL") if language.get("MODEL") else default['model']
            temperature = language.get("TEMPERATURE") if language.get("TEMPERATURE") else default['temperature']
            for api_key in api_keys:
                self.llms.append({
                    "llm": None,
                    "type": key,
                    "base_url":base_url,
                    "api_key":api_key,
                    "model":model,
                    "temperature":temperature,
                    "used":0,
                    "last_used": 0 
                })
        
    def get_embedding(self,key="EMBEDDING.TOGETHER",full=False) :
        if self.embeddings:
            if not key:
                embeddings = self.embeddings
            else:
                embeddings = [item for item in self.embeddings if item['type']==key]
            if embeddings:
                embedding = random.choice(embeddings)    
                if not embedding.get('embedding'):
                    embed_type = embedding['type']
                    if  embed_type == 'EMBEDDING.TOGETHER':
                        embedding['embedding'] = TogetherEmbeddings(api_key = embedding.get('api_key'),model=embedding.get('model'))
                    elif embed_type == "EMBEDDING.GEMINI" :
                        embedding['embedding'] = GoogleGenerativeAIEmbeddings(model=embedding.get('model'),google_api_key=embedding.get('api_key'))
                    else:
                        raise Exception(f"目前不支持{embedding['type']}嵌入模型")
                embedding['used'] = embedding.get('used',0) + 1 
                embedding['last_used'] = time.time()
                if full:
                    return embedding
                else:
                    return embedding['embedding']
        raise Exception("请先调用regist_embedding注册嵌入模型")

    def regist_embedding(self):
        defaults = {
                      "EMBEDDING.TOGETHER": {"model":"BAAI/bge-large-en-v1.5"},
                      "EMBEDDING.GEMINI": {"model":"models/embedding-001"}
                  }
        for key in defaults:
            default = defaults[key]
            embed = self.config.get(key)
            base_url = embed.get("BASE_URL")
            api_keys = embed.get("API_KEYS")
            if api_keys:
                api_keys = api_keys.split(",")
            else:
                api_keys = []
            model= embed.get("MODEL") if embed.get("MODEL") else default['model']
            for api_key in api_keys:
                self.embeddings.append({
                    "embedding": None,
                    "type": key,
                    "base_url": base_url,
                    "api_key":api_key,
                    "model":model,
                    "used":0,
                    "last_used": 0 
                })
    def get_prompt(self,system_prompt=None,placeholder_key=None,human_keys={"input":""},outputParser=None,is_chat = True,use_chinese=True) -> ChatPromptTemplate:
        if not system_prompt:
            system_prompt=""
        if use_chinese:
            system_prompt = f"所有问题请用中文回答\n{system_prompt}"
        if not is_chat:
            human_input_keys = []
            if human_keys:
                human_prompt = ""
                for key in human_keys:
                    human_prompt += f"{human_keys[key]}:{{{key}}}\n" 
                human_input_keys = human_keys.keys()
            if outputParser:
                prompt = PromptTemplate(
                    template=f"{system_prompt}\n{{format_instructions}}\n{human_prompt}",
                    input_variables=human_input_keys,
                    partial_variables={"format_instructions": outputParser.get_format_instructions()}
                )
            else:
                prompt =  PromptTemplate(
                    template=f"{system_prompt}\n{human_prompt}",
                    input_variables=human_input_keys,
                ) 
        else:
            messages = []
            if outputParser:
                partial_prompt = PromptTemplate(template=f"{system_prompt}\n{{format_instructions}}", 
                                                partial_variables={"format_instructions": outputParser.get_format_instructions()})
                #messages.append(("system",partial_prompt.format(**{"format_instructions": outputParser.get_format_instructions() })))
                messages.append(
                    SystemMessagePromptTemplate(prompt=partial_prompt)               
                )
            elif system_prompt:
                messages.append(("system",system_prompt))

            if placeholder_key:
                messages.append(("placeholder", f"{{{placeholder_key}}}"))
            if human_keys:
                human_prompt = ""
                for key in human_keys:
                    human_prompt += f"{human_keys[key]}:{{{key}}}\n"
                messages.append(("human",human_prompt))
            StringLib.logging_in_box(str(messages),console_width=160,print_func=print)
            prompt = ChatPromptTemplate.from_messages(messages)
        return prompt

    def get_outputParser(self,pydantic_object=None):
        if pydantic_object:
            return PydanticOutputParser(pydantic_object=pydantic_object)
        return StrOutputParser()
    
    def get_opengpt4o_client(self,api_key):
        client = Client("KingNish/OpenGPT-4o")
        return client
    def opengpt4o_predict(self, client,prompt="hello",imageUrl=None):
        imageFile = file(imageUrl) if imageUrl else None
        result = client.predict(
                image3=imageFile,
                prompt3=prompt,
                api_name="/predict"
        )
        return result
    def opengpt4o_chat(self,client,prompt="hello",imageUrls=[],temperature=0.5,webSearch=True):
        imageFiles = [file(imageUrl) for imageUrl in imageUrls] if imageUrls else []
        result = client.predict(
            message={"text":prompt,"files":imageFiles},
            request="idefics2-8b-chatty",
            param_3="Top P Sampling",
            param_4=temperature,
            param_5=4096,
            param_6=1,
            param_7=0.9,
            param_8=webSearch,
            api_name="/chat"
        )
        return result
    def get_chatopenai_llm(self,base_url,api_key,model,temperature=0.7):
        llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=model,
                temperature=temperature
                )
        return llm

    def get_ollama_llm(self,base_url,model,temperature=0.7):
        llm = Ollama(
                base_url=base_url,
                model=model,
                temperature=temperature
                )
        return llm

    def get_textsplitter(self,chunk_size=1000,chunk_overlap=10):
        text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
        return text_splitter
    
    def split_markdown_docs(self,text,chunk_size=1000,chunk_overlap=0):
            splited_result = self.split_text_with_protected_blocks(text,chunk_size=chunk_size,chunk_overlap=chunk_overlap)
            # Split
            splited_docs = list(map(lambda item:Document(page_content=item),splited_result))
            return splited_docs
    def extract_blocks(self,text, pattern):
        """通用函数来提取符合模式的块"""
        blocks = pattern.findall(text)
        return blocks
    def replace_blocks_with_placeholders(self,text, blocks, block_type):
        """使用占位符替换块"""
        for i, block in enumerate(blocks):
            text = text.replace(block, f'{{{block_type}_{i}}}')
        return text
    def restore_blocks(self,text, blocks, block_type):
        """将占位符替换回块"""
        for i, block in enumerate(blocks):
            text = text.replace(f'{{{block_type}_{i}}}', block)
        return text
    def split_text(self,text,chunk_size=1000,chunk_overlap=0):
        """你的拆分逻辑，例如按段落拆分"""
        #return text.split('\n\n')
        text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
        # Split
        splited_docs = text_splitter.split_documents([Document(page_content=text)])

        return map(lambda item:item.page_content,splited_docs)
    def split_text_with_protected_blocks(self,text,chunk_size,chunk_overlap):
        # 定义匹配Markdown表格的正则表达式
        #table_pattern = re.compile(
        # r'''
        # (                           # 捕获组
        #     ^\|.*\|[\r\n]+          # 表头行
        #     (?:\|[-\s:]*\|[\r\n]*)  # 分隔行
        #     (?:\|.*\|[\r\n]*)+      # 数据行
        # )
        # ''', 
        # re.MULTILINE | re.VERBOSE
        # )
        table_pattern = re.compile(
        r'''
        (                           # 捕获组
            ^\|.*\|.*$              # 表头行
            (?:\r?\n\|.*\|.*$)+     # 后续行
        )
        ''', 
        re.MULTILINE | re.VERBOSE
        )
        # 定义匹配脚本代码块的正则表达式
        script_pattern = re.compile(r'((?: {4}.+\n)+)', re.MULTILINE)
        #script_pattern = re.compile(r"^(\t|(?:\n))*(?:```)(.*?)```", re.MULTILINE)

        # 提取表格和脚本块
        tables = self.extract_blocks(text, table_pattern)
        scripts = self.extract_blocks(text, script_pattern)
        
        # 用占位符替换表格和脚本块
        text_with_placeholders = self.replace_blocks_with_placeholders(text, tables, 'TABLE')
        text_with_placeholders = self.replace_blocks_with_placeholders(text_with_placeholders, scripts, 'SCRIPT')
        
        FileLib.writeFile("current.md",text_with_placeholders)
        # 拆分文本
        split_parts = self.split_text(text_with_placeholders,chunk_size=chunk_size,chunk_overlap=chunk_overlap)
        
        # 恢复表格和脚本块
        restored_parts = [self.restore_blocks(part, tables, 'TABLE') for part in split_parts]
        restored_parts = [self.restore_blocks(part, scripts, 'SCRIPT') for part in restored_parts]
        
        return restored_parts
    def get_huggingface_embedding(self,mode="BGE"):
        if mode=="BGE":
            embedding = HuggingFaceBgeEmbeddings()
        else:
            embedding = HuggingFaceBgeEmbeddings()
        return embedding
    
    def create_faiss_from_docs(self,docs,embedding=None) -> FAISS:
        if not embedding:
            embedding = self.get_embedding()
        vectorstore = FAISS.from_documents(docs,embedding=embedding)
        return vectorstore
    def create_faiss_from_textes(self,textes,embedding=None) -> FAISS:
        if not embedding:
            embedding = self.get_embedding()
        vectorstore = FAISS.from_texts(textes, embedding=embedding)
        return vectorstore
       
    def save_faiss(self,  db_file:str, vectorstore: FAISS,index_name:str = "index"):
        vectorstore.save_local(db_file,index_name)

    def load_faiss(self, db_file:str ,embedding=None, index_name:str = "index") -> FAISS:
        if not embedding:
            embedding = self.get_embedding()
        vectorestore = FAISS.load_local(db_file, embeddings=embedding, index_name=index_name, allow_dangerous_deserialization=True)
        return vectorestore
    
    def search_faiss(self,query,vectorstore: FAISS,k=10):
        return vectorstore.similarity_search(query,k=k)

def __llm_test(langchainLib:LangchainLib):
    for _ in range(3):
        llm = langchainLib.get_llm("LLM.GROQ")
        res = llm.invoke("hello")
        print("res:",res)
    print("llms:",[(item["type"],item["api_key"],item["used"]) for item in langchainLib.llms])

def __outputParser_test(langchainLib:LangchainLib):
    class Food(BaseModel):
        name: str = Field(description="name of the food")
        place: str = Field(defualt="未指定",description="where to eat food?",examples=["家","公司","体育馆"])
        calories: float|None = Field(title="卡路里(千卡)",description="食物热量")
        amount: tuple[float,str] = Field(description="tuple of the value and unit of the food amount")
        time: str = Field(default = "未指定",description="the time of eating food,确保每个食物都有对应的时间，如果没有指定则为空字符串")
        health: Literal["健康","不健康","未知"]|None = Field(description="根据常识判断食物是否为健康食品",examples=["健康","不健康","未知"])
    class Foods(BaseModel):
        foods: List[Food]

    # Set up a parser + inject instructions into the prompt template.
    parser = langchainLib.get_outputParser(Foods)

    prompt1 = PromptTemplate(
        template="用中文分析句子的内容。如果没有指定食物热量则根据食物的名称和数量进行估计。判断食物是否为健康\n{format_instructions}\n{command}\n",
        input_variables=["command"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )


    # And a query intended to prompt a language model to populate the data structure.
    fixed_parser = OutputFixingParser.from_llm(parser=parser, llm=langchainLib.get_llm('LLM.GROQ'))
    # retry_parser = RetryOutputParser.from_llm(parser=parser, llm=langchainLib.get_llm())

    prompt2 = langchainLib.get_prompt(
            system_prompt = "用中文分析句子的内容。如果没有指定食物热量则根据食物的名称和数量进行估计。同时判断食物是否为健康",
            human_keys={"command":"输入的语句"},
            outputParser = parser,
            is_chat = False
        )

    #chain = prompt2 | langchainLib.get_llm() | fixed_parser
    
    chain = prompt2 | langchainLib.get_llm('LLM.GROQ') | parser
    
    # retry_chain = RunnableParallel(
    #     completion=chain, prompt_value=prompt1,
    #     ) | RunnableLambda(lambda x:retry_parser.parse_with_prompt(**x))

    #output = chain.invoke({"command": "我今天在家吃了3个麦当劳炸鸡和一个焦糖布丁，昨天8点在电影院吃了一盘20千卡的西红柿炒蛋"})
    output = chain.invoke({"command": "两个小时前吃了一根雪糕，还喝了一杯咖啡"})
    #retry_parser.parse_with_prompt(output['completion'], output['prompt_value'])
    #retry_parser.parse_with_prompt(output['completion'],output['prompt_value'])
    print("\noutput parser:",output)

    print("\nllms:",[(item["type"],item["api_key"],item["used"]) for item in langchainLib.llms])


def __runnalble_test(langchainLib:LangchainLib):
    runnable1 = RunnableParallel(
    passed=RunnablePassthrough(),
    modified=lambda x: x["num"] + 1,
    other = RunnableParallel(
        passed=RunnablePassthrough(),
        modified=lambda x: x["num"] * 2,
        )
    )
    #runnable1.invoke({"num":1})
    def f(x):
        return x['modified']*100

    runnable2 = runnable1 | RunnableParallel(
        {"origin": RunnablePassthrough(),
        "new1": lambda x: x["other"]["passed"],
        "new2": RunnableLambda(f)}
        )

    #for trunck in runnable2.stream({"num": 1}):
    #  print(trunck)
    res = runnable2.invoke({"num": 1})
    print("\nrunnalbe:",res)

async def __prompt_test(langchainLib:LangchainLib):

    prompt = langchainLib.get_prompt(f"你对日历时间非常精通",human_keys={"context":"关联的上下文","question":"问题是"},is_chat = True)
    prompt.partial(context="我的名字叫小美")   # 这个为什么不起作用?
    llm = langchainLib.get_llm("LLM.TOGETHER")
    outputParser = langchainLib.get_outputParser()
    chain = prompt | llm | outputParser

    res = await chain.ainvoke({"question":"我叫什么名字，今天礼拜几","context":"我是海涛"})
    print(res)
    res = chain.stream({"question":"用我的名字写一周诗歌","context":"我的名字叫小美"})
    for chunk in res:
        print(chunk,end="")
    
    prompt = PromptTemplate.from_template("用中文回答：{topic} 的{what}是多少")
    chain = prompt | langchainLib.get_llm("LLM.GROQ") | outputParser
    promise = chain.batch([{"topic":"中国","what":"人口"},{"topic":"美国","what":"国土面积"},{"topic":"新加坡","what":"大学"}])
    print(promise)
    print("\n\nllms:",[(item["type"],item["api_key"],item["used"]) for item in langchainLib.llms])

def __rag_test(langchainLib:LangchainLib):
    ###### create vectorestore
    # docs = [Document("I am a student"),Document("who to go to china"),Document("this is a table")]
    # vectorestore = langchainLib.create_faiss_from_docs(docs)
    # langchainLib.save_faiss("faiss.db",vectorestore)
    
    vectorestore = langchainLib.load_faiss("faiss.db")
    print("v--->",langchainLib.search_faiss("I want to buy a table?",vectorestore,k=1))
    
    ###### have bug when poetry add sentence_transformers   
    #v1 = langchainLib.get_huggingface_embedding()
    #print("huggingface BGE:",v1)

    ###### tet google embdeeding
    # embed = langchainLib.get_embedding("EMBEDDING.GEMINI")
    # docs = [Document("I am a student"),Document("who to go to china"),Document("this is a table")]
    # vectorestore = langchainLib.create_faiss_from_docs(docs,embedding=embed)
    # langchainLib.save_faiss("faiss.db",vectorestore,index_name="gemini")
async def __load_test(langchainLib:LangchainLib):
    pass

async def main():
    langchainLib = LangchainLib()
    # StringLib.logging_in_box(f"\n{Color.YELLOW} 测试llm {Color.RESET}")
    # __llm_test(langchainLib)

    StringLib.logging_in_box(f"\n{Color.YELLOW} 测试prompt {Color.RESET}")
    await __prompt_test(langchainLib)    
    
    StringLib.logging_in_box(f"\n{Color.YELLOW} 测试loader {Color.RESET}")
    await __load_test(langchainLib)    

    # StringLib.logging_in_box(f"\n{Color.YELLOW} 测试runnable {Color.RESET}")
    # __runnalble_test(langchainLib)
    
    #StringLib.logging_in_box(f"{Color.YELLOW} 测试outputParser {Color.RESET}")
    #__outputParser_test(langchainLib)
    
    # StringLib.logging_in_box(f"\n{Color.YELLOW} 测试rag {Color.RESET}")
    # __rag_test(langchainLib)

if __name__ == "__main__":
    main()
    
    # markdown_text = readFile("./output1/605aeaf6963a5f13db36dd27533f9ebd.md")
    # split_result = split_text_with_protected_blocks(markdown_text)
    # for index,part in enumerate(split_result):
    #     writeFile(f"test-{index}.md",part)
    
    # 测试hf opengpt4o
    # langchainLib = LangchainLib()
    # client = langchainLib.get_opengpt4o_client("api_key")
    # prompt = """识别图片的类型，返回JSON格式：
    #             {type:图片类型(流程图、架构图、界面图、其他}
    #         """
    # result = langchainLib.opengpt4o_predict(client,
    #                         prompt=textwrap.dedent(prompt),imageUrl=None)
    # print(result)

