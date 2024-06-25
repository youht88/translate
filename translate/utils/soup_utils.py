import re
import json
from bs4 import BeautifulSoup
from bs4.element import Tag, Comment
from utils.crypto_utils import HashLib
from utils.file_utils import *    
import time
import requests
from lxml import etree
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
    def add_tag(cls, soup, tag_name, selectors):
        #为符合selectors(xpath)的元素(第一个)套上tag_name
        #如果已经有tag_name则不会重复嵌套tag_name
        # 返回新的soup
        tree = etree.HTML(str(soup))
        for selector in selectors:
            elems = tree.xpath(selector) 
            if elems:
                elem = elems[0]
                tag_element = etree.Element(tag_name)
                parent = elem.getparent()
                if parent and parent.tag!=tag_name:
                    parent.replace(elem, tag_element)
                    tag_element.append(elem)
                    # parent = elem.getparent()
                    # index = parent.index(elem)
                    # parent.insert(index, tag_element)
        html = etree.tostring(tree).decode()
        
        return cls.html2soup(html)            
    @classmethod
    def remove_tag(cls, soup, tag_name):
        #去除tag_name
        #返回新的soup

        tree = etree.fromstring(str(soup))
        elems = tree.xpath(f"//{tag_name}") 
        for tag_element in elems:
            # 获取 <ignore> 标签的父元素
            parent = tag_element.getparent()
            # 获取 <ignore> 标签的索引
            index = parent.index(tag_element)
            # 将 <ignore> 标签的所有子元素移动到其父元素的相同索引位置
            for child in tag_element:
                tag_element.remove(child)
                parent.insert(index, child)
                index += 1
            # 移除 <ignore> 标签
            parent.remove(tag_element)
        html = etree.tostring(tree).decode()
        return cls.html2soup(html)  
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
    def compare_soup_structure(cls, soup1, soup2):
        """
        比较两个 BeautifulSoup 对象的结构是否完全一致，忽略文本内容。

        Args:
            soup1: 第一个 BeautifulSoup 对象。
            soup2: 第二个 BeautifulSoup 对象。

        Returns:
            bool: 如果结构完全一致则返回 True，否则返回 False。
        """

        def compare_tags(tag1, tag2):
            """
            递归比较两个标签及其子元素的结构，忽略文本内容。

            Args:
                tag1: 第一个标签。
                tag2: 第二个标签。

            Returns:
                bool: 如果结构完全一致则返回 True，否则返回 False。
            """
            if tag1.name != tag2.name:
                return False
            if tag1.attrs != tag2.attrs:
                return False
            if len(tag1.contents) != len(tag2.contents):
                return False
            for i in range(len(tag1.contents)):
                child1 = tag1.contents[i]
                child2 = tag2.contents[i]
                if isinstance(child1, Tag) and isinstance(child2, Tag):
                    if not compare_tags(child1, child2):
                        return False
            return True

        return compare_tags(soup1, soup2)

    @classmethod
    def replace_text_with_dictionary(cls, soup, dictionary={}):
        for element in soup.find_all(text=True):
            if element.parent.name in ['[document]', 'html', 'body']:
                continue  # 跳过顶层元素的文本节点
            if element.strip() and not element.string:
                continue  # 跳过包含子元素的文本节点

            # 尝试替换文本
            new_text = dictionary.get(element.strip())
            if new_text:
                element.replace_with(new_text)
    @classmethod
    def find_all_text(cls, soup,separator='_||_')->list:
        texts = soup.get_text(separator=separator, strip=True)
        if not texts:
            return []
        return texts.split(separator)
    @classmethod
    def walk(cls, soup, func=None,size=200,level=0,blocks=[],ignore_tags=["script","style","ignore"]):
        contents = soup.contents
        length = 0
        nodes = {}
        for idx,node in enumerate(contents):
            is_ignored = False
            if node.name in ignore_tags:
                is_ignored = True
            #print("ignore=",is_ignored,"node.name=",node.name,"level=",level,"idx=",idx,"length=",length,"node=",len(str(node)),str(node)[:50],"...")        
            if not is_ignored:
                length += len(str(node))
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
                nodes = {}

            if not is_ignored:
                if len(str(node)) < size:
                    hash = HashLib.md5(str(time.time()))[:6]
                    nodes[hash]=node
                    length += len(str(node))
                    continue
                else:
                    if isinstance(node, Tag): 
                        cls.walk(node, func=func,size=size,level=level+1,blocks=blocks,ignore_tags=ignore_tags)
                    else:
                        func and  func(node)
        if nodes:
                #print("level=",level,f"replace with block {len(blocks)}")
                nodes_html=""
                for key in nodes:
                    cls.replace_block(nodes[key],BeautifulSoup(f"<div t={key}></div>", 'html.parser'))
                    nodes_html += f"<div t={key}>{nodes[key]}</div>"
                blocks.append(nodes_html)
                nodes = {}
    @classmethod
    def replace_block(cls, source_block, target_block):
        source_block.replace_with(target_block)
    @classmethod
    def unwalk(cls,soup,blocks):
        for idx, block in enumerate(blocks):
            target_block = cls.html2soup(block)
            tnodes = target_block.find_all(lambda tag:tag.has_attr("t"))
            for target_node in tnodes:
                t = target_node.attrs.get("t")
                source_node = soup.find(attrs={"t":t})
                if source_node:
                    source_node.replace_with(target_node.contents[0]) 

if __name__ == "__main__":
    html0 = requests.get("https://global.alipay.com/docs/").text
    html =  FileLib.readFile("pw.html")
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



