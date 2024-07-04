# ######  测试翻译html片段
# print(1,translater.config.get("LLM",{}).get("SILICONFLOW_API_KEY"))
# html = FileLib.readFile("part_13.html")
# print(2,html)
# res = translater.html_chain.invoke({"input":html})
# print(res.content)
#####  测试 playwright
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

# def fix():
#     task = FileLib.loadJson("task.json")
#     task1 = {}
#     for id in task:
#         print(id)
#         url = task[id]["url"]
#         url = url.replace(",","")
#         task[id]["url"] = url
#         md5 = HashLib.md5(url)
#         task1[md5] = task[id]
#     FileLib.dumpJson("task1.json",task1)
