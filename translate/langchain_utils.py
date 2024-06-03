from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.docstore.document import Document
import re
from utils import *

def get_chatopenai_llm(base_url,api_key,model,temperature=0.7):
    llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=temperature
            )
    return llm

def get_ollama_llm(base_url,model,temperature=0.7):
    llm = Ollama(
            base_url=base_url,
            model=model,
            temperature=temperature
            )
    return llm

def get_prompt(system_prompt):
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
def split_markdown_docs(text,chunk_size=1000,chunk_overlap=0):
        splited_result = split_text_with_protected_blocks(text,chunk_size=chunk_size,chunk_overlap=chunk_overlap)
        # Split
        splited_docs = list(map(lambda item:Document(page_content=item),splited_result))
        return splited_docs
def extract_blocks(text, pattern):
    """通用函数来提取符合模式的块"""
    blocks = pattern.findall(text)
    return blocks
def replace_blocks_with_placeholders(text, blocks, block_type):
    """使用占位符替换块"""
    for i, block in enumerate(blocks):
        text = text.replace(block, f'{{{block_type}_{i}}}')
    return text
def restore_blocks(text, blocks, block_type):
    """将占位符替换回块"""
    for i, block in enumerate(blocks):
        text = text.replace(f'{{{block_type}_{i}}}', block)
    return text
def split_text(text,chunk_size=1000,chunk_overlap=0):
    """你的拆分逻辑，例如按段落拆分"""
    #return text.split('\n\n')
    text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    # Split
    splited_docs = text_splitter.split_documents([Document(page_content=text)])

    return map(lambda item:item.page_content,splited_docs)
def split_text_with_protected_blocks(text,chunk_size,chunk_overlap):
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
    tables = extract_blocks(text, table_pattern)
    scripts = extract_blocks(text, script_pattern)
    
    # 用占位符替换表格和脚本块
    text_with_placeholders = replace_blocks_with_placeholders(text, tables, 'TABLE')
    text_with_placeholders = replace_blocks_with_placeholders(text_with_placeholders, scripts, 'SCRIPT')
    
    writeFile("current.md",text_with_placeholders)
    # 拆分文本
    split_parts = split_text(text_with_placeholders,chunk_size=chunk_size,chunk_overlap=chunk_overlap)
    
    # 恢复表格和脚本块
    restored_parts = [restore_blocks(part, tables, 'TABLE') for part in split_parts]
    restored_parts = [restore_blocks(part, scripts, 'SCRIPT') for part in restored_parts]
    
    return restored_parts

if __name__ == "__main__":
    
    markdown_text = readFile("./output1/605aeaf6963a5f13db36dd27533f9ebd.md")
    split_result = split_text_with_protected_blocks(markdown_text)
    for index,part in enumerate(split_result):
        writeFile(f"test-{index}.md",part)


