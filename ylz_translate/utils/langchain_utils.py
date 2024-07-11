import langchain
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from langchain.docstore.document import Document

from langchain_core.prompts import ChatPromptTemplate
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

from gradio_client import Client,file
import re

from .config_utils import Config
from .file_utils import FileLib
import textwrap
import random
import time

class LangchainLib():
    llms:list = []
    embeddings:list  = []
    def __init__(self):
        self.config = Config.get()
        self.regist_llm()
        self.regist_embedding()
    def get_llm(self,key=None) -> dict:
        if self.llms:
            if not key:
                llms = self.llms
            else:
                llms = [item for item in self.llms if item['type']==key]
            if llms:
                llm = random.choice(llms)    
                if not llm.get('llm'):
                    llm['llm'] = ChatOpenAI(
                        base_url=llm.get('base_url'),
                        api_key= llm.get('api_key'),
                        model= llm.get('model'),
                        temperature= llm.get('temperature')
                        )
                llm['used'] = llm.get('used',0) + 1 
                llm['last_used'] = time.time()
                return llm['llm'] 
        raise Exception("请先调用regist_llm注册语言模型")
    def regist_llm(self):
        defaults = {"LLM.TOGETHER":
                      {"model":"Qwen/Qwen1.5-72B-Chat","temperature":0},
                   "LLM.SILICONFLOW":
                      {"model":"alibaba/Qwen1.5-110B-Chat","temperature":0},
                   "LLM.GROQ":
                      {"model":"llama3-70b-8192","temperature":0}
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
                    "last_used": None 
                })
        
    def get_embedding(self,key=None) -> dict:
        if self.embeddings:
            if not key:
                embeddings = self.embeddings
            else:
                embeddings = [item for item in self.embeddings if item['type']==key]
            if embeddings:
                embedding = random.choice(embeddings)    
                if not embedding.get('embedding'):
                    if embedding['type'] == 'EMBEDDING.TOGETHER':
                        embedding['embedding'] = TogetherEmbeddings(api_key = embedding.get('api_key'),model=embedding.get('model'))
                    else:
                        raise Exception(f"目前不支持{embedding['type']}嵌入模型")
                embedding['used'] = embedding.get('used',0) + 1 
                embedding['last_used'] = time.time()
                return embedding['embedding']
        raise Exception("请先调用regist_embedding注册嵌入模型")

    def regist_embedding(self):
        defaults = {"EMBEDDING.TOGETHER":
                      {"model":"BAAI/bge-large-en-v1.5"}
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
                    "api_key":api_key,
                    "model":model,
                    "used":0,
                    "last_used": None 
                })

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

    def get_prompt(self,system_prompt):
        prompt = ChatPromptTemplate.from_messages(
                [
                    
                    (
                        "system",
                        system_prompt,
                    ),
                    ("human", "{input}"),
                ]
            )
        return prompt

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

def main():
    langchainLib = LangchainLib()
    
    # create vectorestore
    # docs = [Document("I am a student"),Document("who to go to china"),Document("this is a table")]
    # vectorestore = langchainLib.create_faiss_from_docs(docs)
    # langchainLib.save_faiss("faiss.db",vectorestore)
    
    vectorestore = langchainLib.load_faiss("faiss.db")
    print("v--->",langchainLib.search_faiss("I want to buy a table?",vectorestore,k=1))
    
    # test llm from cache
    # for i in range(3):
    #     res = langchainLib.get_llm("LLM.GROQ").invoke("hello")
    #     print("res:",res)
    # print("llms:",[(item["type"],item["api_key"],item["used"]) for item in langchainLib.llms])

    # have bug when poetry add sentence_transformers   
    #v1 = langchainLib.get_huggingface_embedding()
    #print("huggingface BGE:",v1)

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

