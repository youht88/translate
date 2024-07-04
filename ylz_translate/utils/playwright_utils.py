import asyncio
from pydoc import writedoc
from playwright.async_api import async_playwright, Browser, Page
import time
from logger import logger
import shlex
from .langchain_utils import *
from .soup_utils import SoupLib
from tqdm import tqdm

class PlaywrightLib:
    def __init__(self, browser_type="chromium", headless=False):
        self.browser_type = browser_type
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.__browser_type = getattr(self.playwright, self.browser_type)
        self.browser: Browser = await self.__browser_type.launch(headless=self.headless)
        self.page: Page = await self.browser.new_page()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()
        await self.playwright.stop()
    async def goto(self, url,timeout=60000,wait_until="load",start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        await self.page.goto(url,timeout=timeout,wait_until=wait_until)
        bool(end_log) and logger.info(end_log)

    async def click(self, selector,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        await self.page.click(selector)
        bool(end_log) and logger.info(end_log)

    async def fill(self, selector, text,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        await self.page.fill(selector, text)
        bool(end_log) and logger.info(end_log)

    async def get_html(self, selector=None, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        if bool(selector):
            elements = await self.page.query_selector_all(f"xpath={selector}")
            content = content = await asyncio.gather(
                *[element.evaluate('el => el.innerHTML') for element in elements]
            )
        else:
            content = [await self.page.content()]
        bool(end_log) and logger.info(end_log)
        return content
    async def replace_html(self, selector=None, innerHTML='<div>HELLO...</div>',start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        if bool(selector):
            elements = await self.page.query_selector_all(f"xpath={selector}")
            await asyncio.gather(
                *[element.evaluate(f'el => el.innerHTML="{innerHTML}"') for element in elements]
            )
            # for element in elements:
            #     print(element)
            #     await self.page.evaluate(
            #         f" (element) => element.innerHTML = ```{innerHTML}``` ", element
            #     )
            # self.page.evaluate(
            #     """(selector) => {
            #         const element = document.querySelector(selector);
            #         if (element) {
            #             element.innerHTML = '<div> hello </div>';
            #         }
            #     }""",
            #     selector,  # 将选择器传递给 JavaScript 函数
            # )
            # element = self.page.locator(selector)
            # print("*"*50,element[0].inner_html())
            # element[0].inner_html = '<div> hello </div>' 
        else:
            await self.page.set_content(innerHTML)
        bool(end_log) and logger.info(end_log)
    async def selector_exists(self, selector) -> bool:
        element = self.page.locator(selector)
        return await element.count() > 0
    async def wait_for_selector(self, selector, timeout=5000,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        await self.page.wait_for_selector(selector, timeout=timeout)
        bool(end_log) and logger.info(end_log)

    async def wait_for_load_state(self, state,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        await self.page.wait_for_load_state(state)
        bool(end_log) and logger.info(end_log)
    
    async def text_content(self, selector, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        text = await self.page.text_content(selector)
        bool(end_log) and logger.info(end_log)
        return text
    async def alltext_content(self, selector, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        elements = await self.page.query_selector_all(f"xpath={selector}")
        textes = list(map(lambda element:element.text_content(), elements))
        bool(end_log) and logger.info(end_log)
        return textes
    
    async def screenshot(self, path="screenshot.png"):
        await self.page.screenshot(path=path)

    def wait(self, milliseconds,start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        time.sleep(milliseconds / 1000)  # 将毫秒转换为秒
        bool(end_log) and logger.info(end_log)
    
    async def close(self):
        await self.browser.close()
        await self.playwright.stop()

    async def get_attributes(self, selector, attribute_names, start_log="",end_log=""):
        bool(start_log) and logger.info(start_log)
        if type(attribute_names)!=list and type(attribute_names)!=tuple:
            attribute_names = [attribute_names]
        attribute_values = await self.page.evaluate(
            """([xpath, attributes]) => {
                const elements = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const values = [];
                for (let i = 0; i < elements.snapshotLength; i++) {
                    const element = elements.snapshotItem(i);
                    attrMap = {}
                    for (let attribute of attributes) {
                        attrMap[attribute] = element.getAttribute(attribute);
                    }
                    values.push(attrMap);
                }
                return values;
            }""",
            (selector,attribute_names),
            
        )
        bool(end_log) and logger.info(end_log)
        return attribute_values
    async def get_html_between_xpaths(self, xpath1, xpath2,include_start=True,include_end=False):
        """获取两个 XPath 之间的 HTML 片段。

        Args:
            xpath1: 第一个 XPath 表达式。
            xpath2: 第二个 XPath 表达式。
            include_start: 是否包含第一个 XPath 匹配的元素。
            include_end: 是否包含第二个 XPath 匹配的元素。
        Returns:
            一个字符串，表示两个 XPath 之间的 HTML 片段，
            如果找不到任何匹配的元素，则返回 None。
        """

        html = await self.page.evaluate(
            """([xpath1, xpath2,include_start,include_end]) => {
                const startNode = document.evaluate(xpath1, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                const endNode = document.evaluate(xpath2, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

                if (!startNode || !endNode) {
                    return null;
                }

                let currentNode = startNode;
                let html = "";
                while (currentNode && currentNode !== endNode) {
                    if (currentNode == startNode && !include_start) {
                       currentNode = currentNode.nextSibling;
                       continue
                    }
                    html += currentNode.outerHTML;
                    currentNode = currentNode.nextSibling;
                }
                if (include_end) {
                    html += endNode.outerHTML; // 包含结束节点
                }

                return html;
            }
            """,
            (xpath1,xpath2,include_start,include_end),
        )        
        return html
    
     
async def main():
    #url = "https://global.alipay.com/docs/ac/ams/payment_agreement"
    #url = "https://global.alipay.com/docs/ac/ams/payment_cashier"
    #url = "https://global.alipay.com/docs/ac/ams/supply_evidence"
    url  = "https://global.alipay.com/docs/ac/ams/api_fund"
    langchainLib = LangchainLib()
    llm = langchainLib.get_chatopenai_llm(
            base_url="https://api.siliconflow.cn/v1",
            api_key="api_key",
            model="alibaba/Qwen1.5-110B-Chat",temperature=0)
    systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。
    现在请将下面的HTML格式文档全部翻译成中文,输出HTML文档。
    要求:
        1、不要有遗漏,简单明了。
        2、特别不要遗漏嵌套的HTML的语法
        3、禁止翻译代码中的JSON的key
        4、保留所有原始的HTML格式
        5、检查翻译的结果,以确保语句通顺
    \n\n"""
    prompt = langchainLib.get_prompt(textwrap.dedent(systemPromptText))
    chain = prompt | llm
    # html = readFile("/Users/youht/source/python/translate/translate/test/Response header.html")
    # async with PlaywrightWrapper(headless=False) as pw:
    #     soup = pw.html2soup(html)
    #     newsoup,attribute_dict = pw.hash_attribute(soup) 
    #     writeFile("newsoup.html",newsoup.prettify())
    #     html_cn = chain.invoke({"input":newsoup.prettify()})
    #     soup_cn = pw.to_soup(html_cn.content)
    #     dumpJson("attribute_dict.json",attribute_dict)
    #     soup_cn= pw.unhash_attribute(soup_cn,attribute_dict)
    #     writeFile("test_cn.html",soup_cn.prettify())
        
    # html_cn = 
    # writeFile("test.html",html_cn.content)
    
    async with PlaywrightLib(headless=False) as pw:
        await pw.goto(url,start_log="开始加载页面",end_log="页面加载完成",wait_until="domcontentloaded")

        # pw.wait_for_selector("#Requestparameters")
        # pw.click('//div[contains(@class,"sandboxSwitch")]//span[text()="Sample Codes"]',start_log='sample1 code')
        # textes = pw.alltext_content('//div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]',
        #                          end_log="获取脚本文本")
        # print(textes)
        # pw.click('//div[contains(@class,"sandboxSwitch")]//span[text()="Run in Sandbox"]',start_log='sample2 code')
        # textes = pw.alltext_content('//div[@id="ace-editor"]//div[@class="ace_content"]//div[contains(@class,"ace_text-layer")]',
        #                          end_log="获取脚本文本")
        # print(textes)
        
        # pw.replace_html("//span[text()='Structure']")    
        attr = await pw.get_attributes("//nav//a",["href","title"])
        print(attr)
        pw.wait(3000,start_log="等待3秒",end_log="等待3秒结束")
        #await pw.replace_html("//h3",innerHTML='<div> 临时替换 </div>')
        html_cn = ""
        with tqdm(total= len(attr)) as pbar:
            for index,item in enumerate(attr):
                start = None
                end = None
                title = None
                if index < len(attr) - 1:
                    start = item.get("href",None)
                    end = attr[index + 1].get("href",None)
                if not start or not end:
                    break  
                start = start[1:]
                end = end[1:]
                title = item.get("title")
                html_snip = await pw.get_html_between_xpaths(f"//*[@id='{start}']",f"//*[@id='{end}']",include_start=True,include_end=False)
                soup_snip = SoupLib.html2soup(html_snip)
                attribute_dict = SoupLib.hash_attribute(soup_snip) 
                hash_html_snip_cn = chain.invoke({"input":pw.soup2html(soup_snip)})
                hash_soup_snip_cn = SoupLib.html2soup(hash_html_snip_cn.content)
                SoupLib.unhash_attribute(hash_soup_snip_cn,attribute_dict)
                html_snip_cn = SoupLib.soup2html(hash_soup_snip_cn)
                html_cn += html_snip_cn
                pbar.update(1)
        FileLib.writeFile("test_cn.html",html_cn)
        # pw.click("//div[@id='Requestparameters']//button//span[contains(text(),'Show all')]",start_log="点击Req Show all按钮")
        # pw.click("//div[@id='Responseparameters']//button//span[contains(text(),'Show all')]",start_log="点击Res Show all按钮")
        # pw.wait_for_selector("//div[@id='Requestparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Req Hide all按钮")
        # pw.wait_for_selector("//div[@id='Responseparameters']//button//span[contains(text(),'Hide all')]",start_log="定位Req Hide all按钮")
        # # 等待页面加载完成 (可选，但建议使用)
        # pw.wait_for_load_state("load") 
        #pw.wait(60000,start_log="等待60秒",end_log="等待结束")
        # writeFile("test.html",pw.get_html())
        await pw.close()

    '''
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
    '''

if __name__ == "__main__":
   asyncio.run(main()) 

