import os
import sys

from logger import logger
import logging
import asyncio


from ylz_translate import MarkdonwAction,ImageAction
from ylz_translate.tools.markdown_translater import MarkdownTranslater
from ylz_translate.tools.json_translater import JsonTranslater
from ylz_translate.tools.html_translater import HtmlTranslater

from ylz_translate.utils.file_utils import FileLib


async def start_task(args): 
    mode = args.mode
    url = args.url
    if not url:
        if args.url_file:
            file_text = FileLib.readFile(args.url_file)
            url = file_text.split("\n")    
    crawlLevel = args.crawl
    only_download = args.only_download
    size = args.size
    clear_error_msg = args.clear_error

    if mode == "markdown": 
        ###### markdown模式
        translater = MarkdownTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.JINA)
        if clear_error_msg:
            translater.clearErrorMsg()
        translater.start(imageAction=ImageAction.MARK)
        translater.start()
    elif mode == "html":
        ###### html模式
        translater = HtmlTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.CRAWLER)
        if clear_error_msg:
            translater.clearErrorMsg()
        await translater.start(size=size,only_download=only_download)
    elif mode == "json":
        ###### json模式
        translater = JsonTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.JINA)
        if clear_error_msg:
            translater.clearErrorMsg()
        translater.start(size=size)
        
def start(args):
    asyncio.run(start_task(args)) 

