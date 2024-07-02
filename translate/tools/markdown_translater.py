from logger import logger
import time
import os
import re
from tqdm import tqdm
import textwrap

from translate.tools.image_translater import ImageTranslater

from translate import Translater, MarkdonwAction, ImageAction
from translate.utils.file_utils import FileLib
from translate.utils.crypto_utils import HashLib
from translate.utils.langchain_utils import LangchainLib

class MarkdownTranslater(Translater):
    def __init__(self,url,crawlLevel=1, markdownAction=MarkdonwAction.JINA,env_file=None):
        super().__init__(url=url,crawlLevel=crawlLevel, markdownAction=markdownAction,env_file=env_file)
        self.langchainLib = LangchainLib()
    # translater = MarkdownTranslater(url= url,crawlLevel=1,markdownAction=MarkdonwAction.JINA)
    # translater.start()
    # url为None，则根据self.taskFilename的任务执行
    # url为单个网址，则根据crawlLevel的层级获取url。其中为0表示当前网址，为1表示当前网页的一级链接，以此类推
    # url为网址数组，则忽略crawlLevel，与self.taskFilename的网址合并任务
    def get_chain(self):
        # llm = get_chatopenai_llm(
        #     base_url="https://api.together.xyz/v1",
        #     api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
        #     model="meta-llama/Llama-3-8b-chat-hf",
        #     temperature=0.2
        #     )
        llm = self.langchainLib.get_chatopenai_llm(
            base_url="https://api.together.xyz/v1",
            api_key= self.config.get("LLM",{}).get("TOGETHER_API_KEY"),
            model="Qwen/Qwen1.5-72B-Chat",temperature=0)
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请将下面的markdown格式文档全部翻译成中文。
        注意:
          1、不要有遗漏,简单明了。
          2、特别不要遗漏嵌套的mardkown的语法
          3、禁止翻译代码中的JSON的key
          4、保留所有空白行,以确保markdown格式正确
          5、检查翻译的结果,以确保语句通顺
        \n\n"""
        prompt = self.langchainLib.get_prompt(textwrap.dedent(systemPromptText))
        chain = prompt | llm
        return chain
    def translate_markdown_text(self,chain,text):
        splits = self.langchainLib.split_markdown_docs(text)
        blocks = list(map(lambda block:block.page_content,splits))
        newBlocks = []
        with tqdm(total= len(blocks)) as pbar:
            for index,block in enumerate(blocks):
                FileLib.writeFile(f"part_{index}.md",block)
                try:
                    #writeFile(f"block_{index}.md",block)
                    if self.dictionary.get(block):
                        return self.dictionary[block]
                    result = chain.invoke(
                        {
                            "input": block,
                        }
                    )
                    content = result.content
                    self.dictionary[text]=content
                    FileLib.writeFile(f"part_{index}_cn.md",content)
                    newBlocks.append(content)
                    pbar.update(1)
                except Exception as e:
                    logger.info(f"error on translate_text({index}):\n{'*'*50}\n[{len(block)}]{block}\n{'*'*50}\n\n")
                    raise e
        return "\n\n".join(newBlocks)
    def start(self, imageAction:ImageAction|None=None):
        total = len(self.url)
        logger.info(f"begin on {total} urls")
        startTime = time.time()
        chain = self.get_chain()
        for index,url in enumerate(self.url):
            try:
                id = HashLib.md5(url)
                taskItem = self.task.get(id)
                if not taskItem:
                    taskItem = {
                        "url": url,
                        "metadata": None,
                        "markdownAction": str(self.markdownAction),
                    }
                    self.task[id] = taskItem
                if taskItem.get('errorMsg'):
                    logger.info(f"skip on url={url},id={id} ,because it is error ")
                    continue
                if not os.path.exists(f"{id}.md"):
                    logger.info(f"提取markdown url= {url},id={id} ...")
                    response = self.getMarkdown(url)
                    originHtml = response.get("html",None)
                    originMarkdown = response.get("content",None)
                    metadata = response.get("metadata",None)
                    if originMarkdown:
                        FileLib.writeFile(f"{id}.md",originMarkdown)
                        image_links = re.findall(r"!\[(.*?)\]\((.*?)\)",originMarkdown)
                        taskItem["imageLinks"] = list(map(lambda item:[item[0],item[1],HashLib.md5(item[1])],image_links))
                    if originHtml:
                        FileLib.writeFile(f"{id}.html",originHtml)
                    if metadata:
                        taskItem["metadata"] = metadata
                    taskItem["markdownAction"] = str(self.markdownAction)
                else:
                    originMarkdown = FileLib.readFile(f"{id}.md")
                resultMarkdown = None
                if not os.path.exists(f"{id}_cn.md"):
                    logger.info(f"开始翻译 url= {url},id={id} ...")
                    resultMarkdown = self.translate_markdown_text(chain,originMarkdown)
                    FileLib.writeFile(f"{id}_cn.md",resultMarkdown)
                else:
                    resultMarkdown = FileLib.readFile(f"{id}_cn.md")
                if resultMarkdown and imageAction:
                    if not self.imageTranslater:
                        self.imageTranslater = ImageTranslater()
                    if imageAction==ImageAction.REPLACE:
                        with tqdm(total= len(taskItem["imageLinks"])) as pbar: 
                            for imageLink in taskItem["imageLinks"]:
                                self.imageTranslater.start(imageLink[1],mode="replace")
                                resultMarkdown = self.replace_img_link(imageLink[1],resultMarkdown)
                                pbar.update(1)
                    elif imageAction==ImageAction.MARK:
                        with tqdm(total= len(taskItem["imageLinks"])) as pbar: 
                            for imageLink in taskItem["imageLinks"]:
                                self.imageTranslater.start(imageLink[1],mode="mark")
                                resultMarkdown = self.replace_img_link(imageLink[1],resultMarkdown)
                                pbar.update(1)
                    FileLib.writeFile(f"{id}_cn.md",resultMarkdown)
                endTime = time.time() - startTime
                logger.info(f"[{round((index+1)/total*100,2)}%][累计用时:{round(endTime/60,2)}分钟]===>url->{url},id->{id}")
            except Exception as e:
                taskItem["errorMsg"] = str(e)
                logger.info(f"error on url={url},id={id},error={str(e)}")
                #raise e
        FileLib.dumpJson(self.dictionaryFilename,self.dictionary)
        FileLib.dumpJson(self.taskFilename,self.task)
        if imageAction and self.imageTranslater:
            self.imageTranslater.save()
    def replace_img_link(self,url,text):
        # 正则表达式模式，匹配 Markdown 图片语法 ![alt_text](image_url)
        pattern = re.compile(r'!\[([^\]]*)\]\(' + re.escape(url) + r'\)')
        # 使用新的链接替换所有旧的链接
        imageId = HashLib.md5(url)
        imageTask = self.imageTranslater.get_task_by_id(imageId)
        if imageTask:
            if imageTask['mode']=='replace':
                imageMode = 'r'
            else:
                imageMode = 'm'
            imageType = imageTask['imageType']
            result = text
            if imageType and imageType=='svg':
                newImageLink = f"./img_{imageMode}_{imageId}.{imageType}"
                result = pattern.sub(r'![\1](' + newImageLink + r')', text)
        return result
    def fix_markdown_script(self,markdown):
        pattern = re.compiler(r'copy\n(.*)X{512}')
        return pattern.sub(pattern,markdown)
    def fix_markdown_table(self,markdown):
        pass                      
