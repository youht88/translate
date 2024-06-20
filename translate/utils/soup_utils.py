import re
import json
from bs4 import BeautifulSoup
from bs4.element import Tag
from crypto_utils import HashLib
from file_utils import *    

class SoupLib():
    @classmethod
    def html2soup(cls, html):
        #提取被```html包裹的部分，如果没有则转换整个html
        p=r"```html\n(.*?)\n```"
        res = re.findall(p,html,re.DOTALL)
        if res:
            return BeautifulSoup(res[0], "html.parser")
        else:
            return BeautifulSoup(html, "html.parser")
    @classmethod
    def soup2html(cls, soup):
        return soup.prettify()
    @classmethod
    def hash_attribute(cls, soup, key = 'hash',length=6):
        # 将soup中的所有标签的属性转化为hash，返回attribute_map且原soup已经变更
        attribute_dict = {}
        for tag in soup.find_all(True):  # 查找所有标签
            if tag.attrs:  # 如果标签有属性
                # 将属性字典转换为 "key1='value1' key2='value2'" 格式的字符串
                original_attributes = json.dumps(tag.attrs)

                # 计算 MD5 哈希值
                if length:
                    hash_value = HashLib.md5(original_attributes)[:length]
                else:
                    hash_value = HashLib.md5(original_attributes)

                # 保存原始属性到字典
                attribute_dict[hash_value] = original_attributes

                # 修改标签属性
                tag.attrs.clear()  # 清除所有现有属性
                tag.attrs[key] = hash_value

        return attribute_dict
    @classmethod
    def unhash_attribute(cls,soup, attribute_dict, key = 'hash'):
        # 根据attribute_map还原soup
        for tag in soup.find_all(True):
            if key in tag.attrs:
                hash_value = tag.attrs[key]
                if hash_value in attribute_dict:
                    # 从字典中获取原始属性
                    original_attributes = json.loads(attribute_dict[hash_value])

                    # 还原原始属性
                    tag.attrs.clear()  # 清除现有属性
                    tag.attrs.update(original_attributes)
    @classmethod
    def walk(cls, soup, func=None,size=200,level=0,blocks=[]):
        contents = soup.contents
        length = 0
        nodes={}
        for idx,node in enumerate(contents):
            length += len(str(node))
            #print("level=",level,"length=",length,"node=",len(str(node)),str(node)[:50],"...",str(node)[-50:])
            if length < size:
                hash = HashLib.md5(str(node))[:6]
                nodes[hash]=node
                continue
            length = 0
            if nodes:
                blocks.append(nodes)
                # for key in nodes:
                #     cls.replace_block(nodes[key],BeautifulSoup(f"<R t={key}></R>", 'html.parser'))
                s=""
                for key in nodes:
                    s += str(nodes[key])
                hash = HashLib.md5(s)[:6]    
                cls.replace_block(list(nodes.values()),BeautifulSoup(f"<R t={hash}></R>", 'html.parser'))
            nodes={}
            if len(str(node)) < size:
                hash = HashLib.md5(str(node))[:6]
                nodes[hash]=node
                continue
            else:
                if isinstance(node, Tag): 
                    level+=1
                    cls.walk(node, func=func,size=size,level=level,blocks=blocks)
                else:
                    func & func(node)
        if nodes:
            blocks.append(nodes)
            # for key in nodes:
            #     cls.replace_block(nodes[key],BeautifulSoup(f"<R t={key}></R>", 'html.parser'))
            s=""
            for key in nodes:
                s += str(nodes[key])
            hash = HashLib.md5(s)[:6]    
            cls.replace_block(list(nodes.values()),BeautifulSoup(f"<R t={hash}></R>", 'html.parser'))
    @classmethod
    def replace_block(cls, source_block, target_block):
        """将原始文本块(或连续的多个并列的文本快)替换为更新后的文本块."""
        if type(source_block)!=list:
            source_block = [source_block]
        parent = source_block[0].parent
        if parent:
            index = parent.index(source_block[0])
            parent.insert(index, target_block)
            for block in source_block:
                block.extract()
if __name__ == "__main__":
    html =  FileLib.readFile("test.html")
    soup = SoupLib.html2soup(html)
    hash_dict = SoupLib.hash_attribute(soup)
    blocks = []
    def do(node):
        print(len(str(node)),str(node))
    SoupLib.walk(soup, func = lambda node: do(node),size=800,blocks=blocks)
    # blocks=[]
    # soup1,hash_dict = SoupLib.hash_attribute(soup)
    # for source_block in soup1.contents:
    #     target_block = BeautifulSoup(str(source_block), 'html.parser').contents[0]
    #     target_block.attrs['ok'] = 1
    #     SoupLib.replace_block(source_block,target_block)
    # print(soup1)
    print(soup)
    
    print("="*50)
    for idx,block in enumerate(blocks):
        print(idx,block,end="\n\n")