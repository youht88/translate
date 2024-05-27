from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_chatopenai_llm(base_url,api_key,model,temperature=0.7):
    llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=temperature
            )
    return llm

def get_ollama_llm(base_url,api_key,model,temperature=0.7):
    llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
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
def split_markdown_docs(text,chunk_size=2000,chunk_overlap=0):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on,strip_headers=False)
        docs = markdown_splitter.split_text(text)
        chunk_size = 2000
        chunk_overlap = 0
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        # Split
        splited_docs = text_splitter.split_documents(docs)
        return splited_docs