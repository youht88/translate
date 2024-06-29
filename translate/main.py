import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取 translate 目录的父目录
parent_dir = os.path.dirname(current_dir)
#print("parent_dir",parent_dir)
sys.path.append(parent_dir)
#print(sys.path)

from logger import logger
import logging
from logging.handlers import TimedRotatingFileHandler
import asyncio
import argparse

from translate import MarkdonwAction,ImageAction
from translate.tools.markdown_translater import MarkdownTranslater
from translate.tools.json_translater import JsonTranslater
from translate.tools.html_translater import HtmlTranslater

from translate.utils.data_utils import JsonLib
from translate.utils.file_utils import FileLib


async def main():
     # 分析命令行参数
    parser = argparse.ArgumentParser(description="渐进式翻译系统")
    parser.add_argument("--mode",type=str,required=True,choices=["markdown","html","json"],help="翻译操作模式")
    parser.add_argument("--url",type=str,help="url地址,如果不指定则从--url_file文件获取")
    parser.add_argument("-f","--url_file",type=str,help="包含一行或多行url的文件,指定url时忽略此参数")
    parser.add_argument("--crawl",type=int,default=0,choices=[0,1,2,3],help="爬取网页的层级深度,默认:0,表示仅当前网页")
    parser.add_argument("--only_download",type=bool,default=False,help="仅下载网页html,不进行翻译。默认:False (json模式该参数不起作用)")
    parser.add_argument("-s","--size",type=int,default=1500,help="切分文件的字节大小,默认:1500")
    parser.add_argument("-c","--clear_error",action="store_true",help="清除task.json文件中的错误信息,默认:False")
    parser.add_argument("--log_level",type=str,default="INFO",choices=["INFO","DEBUG"],help="日志级别,默认:INFO")
    parser.add_argument("--log",type=str,default="task.log",help="日志文件名称")
    
    #parser.add_argument("-markdown_action",type=str)
    args = parser.parse_args()
    logger.info(f"参数:{args}")

    # 设置logger
    if args.log_level == "INFO":
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    file_handler = TimedRotatingFileHandler(
        filename=args.log,
        when="midnight",  # 每天午夜滚动
        interval=1,  # 滚动间隔为 1 天
        backupCount=7,  # 保留 7 天的日志文件
    )
    #file_handler = logging.FileHandler("task.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
 
    mode = args.mode
    url = args.url
    if not url:
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
        
    # ######  测试翻译html片段
    # print(1,translater.config.get("LLM",{}).get("SILICONFLOW_API_KEY"))
    # html = FileLib.readFile("part_13.html")
    # print(2,html)
    # res = translater.html_chain.invoke({"input":html})
    # print(res.content)
    ##### playwright
    '''
    async with PlaywrightLib(headless=False) as pw:
        await pw.goto(url,start_log="开始加载页面",end_log="页面加载完成",wait_until="domcontentloaded")
        pw.wait(3000,start_log="等待3秒",end_log="等待结束")
        print(await pw.selector_exists('//section[contains(@class,"right")]'))
        request_show = await pw.selector_exists("//div[@id='Requestparameters']//button//span[contains(text(),'Show all')]")
        if request_show:
            await pw.click("//div[@id='Requestparameters']//button//span[contains(text(),'Show all')]",start_log="点击Req Show all按钮")
        response_show = await pw.selector_exists("//div[@id='Responseparameters']//button//span[contains(text(),'Show all')]")
        if response_show:
            await pw.click("//div[@id='Responseparameters']//button//span[contains(text(),'Show all')]",start_log="点击Res Show all按钮")
        pw.wait(3000,start_log="等待3秒",end_log="等待结束")
        if request_show:
            await pw.wait_for_selector("//div[@id='Requestparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Req Hide all按钮")
        if response_show:
            await pw.wait_for_selector("//div[@id='Responseparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Res Hide all按钮")
        html = await pw.get_html()
        FileLib.writeFile("pw.html",html[0])
        pw.wait(10000,start_log="等待10秒",end_log="等待结束")
    
        await pw.close()
        html = [FileLib.readFile("pw.html")]
        soup = SoupLib.html2soup(html[0])
        hash_dict = SoupLib.hash_attribute(soup)
        blocks = []
        SoupLib.walk(soup, size=2000,blocks=blocks)
        print(len(blocks))
        for idx,item in enumerate(blocks):
            temp = SoupLib.html2soup(item)
            if temp.text:
                print(idx,len(item))
            #FileLib.writeFile(f"pw_{idx}.html",item)
    '''
    # html = FileLib.readFile("pw.html")
    # soup = SoupLib.html2soup(html)
    # soup = SoupLib.add_tag(soup,"ignore",['//section[contains(@class,"right")]'])
    # #soup2 = SoupLib.remove_tag(soup,"ignore")
    # hash_dict = SoupLib.hash_attribute(soup)
    # blocks = []
    # SoupLib.walk(soup, size=2000,blocks=blocks,ignore_tags= ["script", "style", "ignore","svg"])
    # #print("*"*20,soup,"*"*20)
    # print(len(blocks))
    # for idx,block in enumerate(blocks):
    #     print(idx,len(block),len(SoupLib.find_all_text(SoupLib.html2soup(block))))
    # print("*"*20,)
    # idx = 16
    # FileLib.writeFile(f"block{idx}.html",blocks[idx])
    # print(SoupLib.html2soup(blocks[idx]).get_text(separator='||', strip=True))
    # #content = translater.html_chain.invoke({"input":blocks[idx]}).content
    # print("*"*20)
    # #print(SoupLib.html2soup(content).get_text(separator='||', strip=True))
    # for i,item in enumerate(SoupLib.find_all_text(SoupLib.html2soup(blocks[idx]))):
    #     print(i,item)
    # dictionary = {"Array":"列表","is":"是"}
    # soup1 = SoupLib.html2soup(blocks[idx])
    # #soup1.contents[0].attrs={"t":"abcdef"}
    # soup2 = SoupLib.html2soup(blocks[idx])
    # SoupLib.replace_text_with_dictionary(soup2,dictionary)
    # print(soup1,"\n\n",soup2)
    # print(SoupLib.compare_soup_structure(soup1,soup2))
    # translater.update_dictionary(soup1,soup2)
    # print(translater.dictionary)

    #for idx,block in enumerate(blocks):
    #    FileLib.writeFile(f"pw_{idx}.html",block)

    '''
    #表格
    //div[@data-lake-card="table"]
    #代码段
    //div[@data-lake-card="codeblock"]
    #图片
    //span[@data-lake-card="image"]
    #右侧侧边导航
    //nav
    #左侧菜单导航
    //aside
    #主内容
    //article

    # 要翻译的部分
    //article[@class="ant-typography"]//section
    # sandboxSwitch span按钮
    //div[contains(@class,"sandboxSwitch")]//span[text()="Sample Codes"]
    //div[contains(@class,"sandboxSwitch")]//span[text()="Run in Sandbox"]
    #脚本文本
    //div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]
    #定位id
    //*[@id="3RxeL"]
    //*[@id="d8Mc5"]

    # 参数name/type/required
    //h4[starts-with(@id,"Requestparameters")]/span[starts-with(@class,"name")]
    //h4[starts-with(@id,"Requestparameters")]/span[starts-with(@class,"type")]
    //h4[starts-with(@id,"Requestparameters")]/span[starts-with(@class,"required")]
    //h4[starts-with(@id,"Responseparameters")]/span[starts-with(@class,"name")]
    //h4[starts-with(@id,"Responseparameters")]/span[starts-with(@class,"type")]
    //h4[starts-with(@id,"Responseparameters")]/span[starts-with(@class,"required")]
    '''
    
if __name__ == "__main__":   
    asyncio.run(main()) 