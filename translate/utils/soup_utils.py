import re
import json
from bs4 import BeautifulSoup
from bs4.element import Tag, Comment
from utils.crypto_utils import HashLib
from utils.file_utils import *    
import time
import requests

class SoupLib():
    @classmethod
    def html2soup(cls, html):
        #提取被```html包裹的部分，如果没有则转换整个html
        p=r"```html\n(.*?)\n```"
        res = re.findall(p,html,re.DOTALL)
        if res:
            soup =  BeautifulSoup(res[0], "html.parser")
        else:
            soup = BeautifulSoup(html, "html.parser")
        # 将标签外部的多个空白字符替换成一个空格
        for element in soup.find_all(string=True):
            if element.parent.name not in ['script', 'style']:  # 忽略 <script> 和 <style> 标签内的内容
                element.replace_with(BeautifulSoup(" ".join(element.split()), 'html.parser'))
        return soup
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
    def walk(cls, soup, func=None,size=200,level=0,blocks=[],ignore_tags=["script","style"]):
        contents = soup.contents
        length = 0
        nodes = {}
        for idx,node in enumerate(contents):
            if node.name in ignore_tags:
                continue
            length += len(str(node))
            #print("level=",level,"idx=",idx,"length=",length,"node=",len(str(node)),str(node)[:50],"...")
            if length < size:
                hash = HashLib.md5(str(time.time()))[:6]
                nodes[hash]=node
                continue
            length = 0
            if nodes:
                #print("level=",level,f"replace with block {len(blocks)}")
                nodes_html=""
                for key in nodes:
                    cls.replace_block(nodes[key],BeautifulSoup(f"<div t={key}></div>", 'html.parser'))
                    nodes_html += f"<div t={key}>{nodes[key]}</div>"
                blocks.append(nodes_html)
            nodes={}
            if len(str(node)) < size:
                hash = HashLib.md5(str(time.time()))[:6]
                nodes[hash]=node
                length += len(str(node))
                continue
            else:
                if isinstance(node, Tag): 
                    cls.walk(node, func=func,size=size,level=level+1,blocks=blocks)
                else:
                    func and  func(node)
        if nodes:
            #print("level=",level,f"replace with block {len(blocks)}")
            nodes_html=""
            for key in nodes:
                cls.replace_block(nodes[key],BeautifulSoup(f"<div t={key}></div>", 'html.parser'))
                nodes_html += f"<div t={key}>{nodes[key]}</div>"
            blocks.append(nodes_html)
    @classmethod
    def replace_block(cls, source_block, target_block):
        source_block.replace_with(target_block)
    @classmethod
    def unwalk(cls,soup,blocks):
        for block in blocks:
            target_block = cls.html2soup(block)
            tnodes = target_block.find_all(lambda tag:tag.has_attr("t"))
            for target_node in tnodes:
                t = target_node.attrs.get("t")
                source_node = soup.find(attrs={"t":t})
                #print(t,source_node,len(target_node.contents))
                source_node.replace_with(target_node.contents[0]) 

if __name__ == "__main__":
    html = requests.get("https://global.alipay.com/docs/").text
    html1 =  FileLib.readFile("test.html")
    html2 = """
<body>
  <div>
    hello world!!
    厦门
    漳州
    泉州
    <h1> 对话 <em> 重点 </em>   </h1>

    
    <p> let's go to home </p>
    <p> ok, that is fine </p>
  </div>
  <div>
    <h1> 其他测试 </h1>
    <div> 
    </div>
    <div> <p> I am a student!</p></div>
  </div>
  <script>
    var a = 1;
    var b = 2;

  </script>
</body>
"""
    soup = SoupLib.html2soup(html)
    hash_dict = SoupLib.hash_attribute(soup)
    blocks = []
    SoupLib.walk(soup, size=800,blocks=blocks)
    print("="*20)
    #print(soup)
    FileLib.writeFile("soup1.html",SoupLib.soup2html(soup))
    print("="*50)
    for idx,block in enumerate(blocks):
        print(idx,block)

    print("="*80)
    SoupLib.unwalk(soup,blocks)
    SoupLib.unhash_attribute(soup,hash_dict)
    #print(soup.prettify())
    FileLib.writeFile("soup2.html",SoupLib.soup2html(soup))



