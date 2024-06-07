import asyncio
from playwright.sync_api import sync_playwright, Browser, Page
import time
from utils import *
from logger import logger
import shlex
class PlaywrightWrapper:
    def __init__(self, browser_type="chromium", headless=False):
        self.playwright = sync_playwright().start()
        self.browser_type = getattr(self.playwright, browser_type)
        self.browser: Browser = self.browser_type.launch(headless=headless)
        self.page: Page = self.browser.new_page()

    def goto(self, url,timeout=60000,wait_until="load",start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        self.page.goto(url,timeout=timeout,wait_until=wait_until)
        bool(end_log) and logger.info(end_log)

    def click(self, selector,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        self.page.click(selector)
        bool(end_log) and logger.info(end_log)

    def fill(self, selector, text,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        self.page.fill(selector, text)
        bool(end_log) and logger.info(end_log)

    def get_html(self, selector=None, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        if bool(selector):
            elements = self.page.query_selector_all(f"xpath={selector}")
            content = list(map(lambda element:element.inner_html(), elements))
        else:
            content =  self.page.content()
        bool(end_log) and logger.info(end_log)
        return content
    def replace_html(self, selector=None, innerHTML='<div>to \'be\' "replaced"...</div>',start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        if bool(selector):
            elements = self.page.query_selector_all(f"xpath={selector}")
            for element in elements:
                self.page.evaluate(
                    f" (element) => element.innerHTML = ```{innerHTML}``` ", element
                )
        else:
            self.page.set_content(innerHTML)
        bool(end_log) and logger.info(end_log)
    
    def wait_for_selector(self, selector, timeout=5000,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        self.page.wait_for_selector(selector, timeout=timeout)
        bool(end_log) and logger.info(end_log)

    def wait_for_load_state(self, state,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        self.page.wait_for_load_state(state)
        bool(end_log) and logger.info(end_log)
    
    def text_content(self, selector, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        text = self.page.text_content(selector)
        bool(end_log) and logger.info(end_log)
        return text
    def alltext_content(self, selector, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        elements = self.page.query_selector_all(f"xpath={selector}")
        textes = list(map(lambda element:element.text_content(), elements))
        bool(end_log) and logger.info(end_log)
        return textes
    
    def screenshot(self, path="screenshot.png"):
        self.page.screenshot(path=path)

    def wait(self, milliseconds,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        time.sleep(milliseconds / 1000)  # 将毫秒转换为秒
        bool(end_log) and logger.info(end_log)
    def close(self):
        self.browser.close()
        self.playwright.stop()

if __name__ == "__main__":
    #url = "https://global.alipay.com/docs/ac/ams/payment_agreement"
    #url = "https://global.alipay.com/docs/ac/ams/payment_cashier"
    url = "https://global.alipay.com/docs/ac/ams/supply_evidence"
    pw = PlaywrightWrapper(headless=False)
    pw.goto(url,start_log="开始加载页面",end_log="页面加载完成",wait_until="domcontentloaded")
    pw.wait_for_selector("#Requestparameters")
    pw.click('//div[contains(@class,"sandboxSwitch")]//span[text()="Sample Codes"]',start_log='sample1 code')
    textes = pw.alltext_content('//div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]',
                             end_log="获取脚本文本")
    print(textes)
    pw.click('//div[contains(@class,"sandboxSwitch")]//span[text()="Run in Sandbox"]',start_log='sample2 code')
    textes = pw.alltext_content('//div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]',
                             end_log="获取脚本文本")
    print(textes)
    pw.replace_html("//span[text()='Structure']")    
    # pw.click("//div[@id='Requestparameters']//button//span[contains(text(),'Show all')]",start_log="点击Req Show all按钮")
    # pw.click("//div[@id='Responseparameters']//button//span[contains(text(),'Show all')]",start_log="点击Res Show all按钮")
    # pw.wait_for_selector("//div[@id='Requestparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Req Hide all按钮")
    # pw.wait_for_selector("//div[@id='Responseparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Req Hide all按钮")
    # # 等待页面加载完成 (可选，但建议使用)
    # pw.wait_for_load_state("load") 
    pw.wait(60000,start_log="等待60秒",end_log="等待结束")
    # writeFile("test.html",pw.get_html())
    pw.close()

    '''
     # 要翻译的部分
     //article[@class="ant-typography"]//section
     # sandboxSwitch span按钮
     //div[contains(@class,"sandboxSwitch")]//span[text()="Sample Codes"]
     //div[contains(@class,"sandboxSwitch")]//span[text()="Run in Sandbox"]
     #脚本文本
     //div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]
    '''

