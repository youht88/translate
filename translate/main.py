import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取 translate 目录的父目录
parent_dir = os.path.dirname(current_dir)
print("parent_dir",parent_dir)
sys.path.append(parent_dir)
print(sys.path)

from logger import logger
import logging
from logging.handlers import TimedRotatingFileHandler
import asyncio

from translate import MarkdonwAction,ImageAction
from translate.tools.markdown_translater import MarkdownTranslater
from translate.tools.json_translater import JsonTranslater
from translate.tools.html_translater import HtmlTranslater

from translate.utils.data_utils import JsonLib
from translate.utils.file_utils import FileLib


async def main():
    logger.setLevel(logging.INFO)
    file_handler = TimedRotatingFileHandler(
        filename="task.log",
        when="midnight",  # 每天午夜滚动
        interval=1,  # 滚动间隔为 1 天
        backupCount=7,  # 保留 7 天的日志文件
    )
    #file_handler = logging.FileHandler("task.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    crawlLevel = 0
    if len(sys.argv) > 2:
        crawlLevel = int(sys.argv[2])
    if not url:
        url = ["https://global.alipay.com/docs/ac/ams/authconsult",
            "https://global.alipay.com/docs/ac/ams/notifyauth",
            "https://global.alipay.com/docs/ac/ams/accesstokenapp",
            "https://global.alipay.com/docs/ac/ams/authrevocation",
            "https://global.alipay.com/docs/ac/ams/vaulting_session",
            "https://global.alipay.com/docs/ac/ams/vault_method",
            "https://global.alipay.com/docs/ac/ams/notify_vaulting",
            "https://global.alipay.com/docs/ac/ams/inquire_vaulting",
            "https://global.alipay.com/docs/ac/ams/consult",
            "https://global.alipay.com/docs/ac/ams/payment_cashier",
            "https://global.alipay.com/docs/ac/ams/session_cashier",
            "https://global.alipay.com/docs/ac/ams/capture",
            "https://global.alipay.com/docs/ac/ams/payment_agreement",
            "https://global.alipay.com/docs/ac/ams/createpaymentsession_easypay",
            "https://global.alipay.com/docs/ac/ams/paymentrn_online",
            "https://global.alipay.com/docs/ac/ams/notify_capture",
            "https://global.alipay.com/docs/ac/ams/paymentri_online",
            "https://global.alipay.com/docs/ac/ams/paymentc_online",
            "https://global.alipay.com/docs/ac/ams/create_sub",
            "https://global.alipay.com/docs/ac/ams/notify_sub",
            "https://global.alipay.com/docs/ac/ams/notify_subpayment",
            "https://global.alipay.com/docs/ac/ams/change_sub",
            "https://global.alipay.com/docs/ac/ams/cancel_sub",
            "https://global.alipay.com/docs/ac/ams/accept",
            "https://global.alipay.com/docs/ac/ams/supply_evidence",
            "https://global.alipay.com/docs/ac/ams/download",
            "https://global.alipay.com/docs/ac/ams/notify_dispute",
            "https://global.alipay.com/docs/ac/ams/refund_online",
            "https://global.alipay.com/docs/ac/ams/notify_refund",
            "https://global.alipay.com/docs/ac/ams/ir_online",
            "https://global.alipay.com/docs/ac/ams/declare",
            "https://global.alipay.com/docs/ac/ams/inquirydeclare"
            ]
        
    ###### markdown模式
    # translater = MarkdownTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.JINA)
    # translater.clearErrorMsg()
    # translater.start(imageAction=ImageAction.MARK)
    # #translater.start()

    # ###### html模式
    # translater = HtmlTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.CRAWLER)
    # #translater.clearErrorMsg()
    # #await translater.start(size=2000,only_download=True)
    # await translater.start(size=2000)
    
    ####### json模式
    # url = "https://global.alipay.com/docs/ac/ams/authconsult"
    # translater = JsonTranslater(url=url,crawlLevel=crawlLevel, markdownAction=MarkdonwAction.CRAWLER)
    # translater.clearErrorMsg()
    # #await translater.start(size=2000,only_download=True)
    # translater.start(size=2000)
    
    ###### 测试json片段
    json_data = FileLib.loadJson("b.json")
    updates=[]
    updates += JsonLib.find_key_value_path(json_data,"description")
    updates += JsonLib.find_key_value_path(json_data,"x-result.[].message")
    updates += JsonLib.find_key_value_path(json_data,"x-result.[].action") #actionLake
    updates += JsonLib.find_key_value_path(json_data,"x-more") #x-more-lake

    print(len(updates))
    FileLib.dumpJson("a.json",updates)
    
    updates1=[]
    updates1 += JsonLib.find_key_value_path(json_data,"properties.*.description") #descriptionLake
    # updates += JsonLib.find_key_value_path(json_data,"codeDetails.description") #descriptionLake
    #updates += JsonLib.find_key_value_path(json_data,"properties.displayType.description") #descriptionLake
    #updates += JsonLib.find_key_value_path(json_data,"properties.codeValue.description") #descriptionLake
    #updates += JsonLib.find_key_value_path(json_data,"properties.displayType.description") #descriptionLake
    print(len(updates1))
    FileLib.dumpJson("c.json",updates1)

    # ######  测试翻译html片段
    # print(1,translater.config.get("LLM",{}).get("SILICONFLOW_API_KEY"))
    # html = FileLib.readFile("part_13.html")
    # print(2,html)
    # res = translater.html_chain.invoke({"input":html})
    # print(res.content)
    #llm = ChatOpenAI(base_url="https://api.together.xyz/v1",api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",model="Qwen/Qwen1.5-72B-Chat")
    #llm.invoke("hello")
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