
from PIL import Image
import requests
from io import BytesIO
from IPython.display import HTML, display
import base64

from translate.utils.image_utils import *
from translate.utils.langchain_utils import *
class Llava():
    def __init__(self):
        langchainLib = LangchainLib()
        self.llm = langchainLib.get_ollama_llm(
            base_url = "http://youht.cc:18034",
            model="llava:34b",
            temperature=0
        )
    def start(self,image):
        image_b64 = convert_to_base64(image)
        llm_with_image_context = self.llm.bind(images=[image_b64])
        #query_chain = llm_with_image_context.invoke("你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请把这张图原原本本的英文文字找出来")
        #query_result = llm_with_image_context.invoke("请输出这张图片的类型,仅包括以下分类：架构图、流程图、UML图、ER图、时序图、用例图、界面图、截图、表格、公式、源代码、其他")
        query_result = llm_with_image_context.invoke("请提取这张图片的英文")
        return query_result

if __name__ == "__main__":
    llava = Llava()    
    url = "https://idocs-assets.marmot-cloud.com/storage/idocs87c36dc8dac653c1/1693280802335-b70b74e9-8236-41e9-8d97-76caac1acfe3.png"
    image,image_type  = get_url_image(url)
    print("image_type:",image_type)
    print("llm:",llava.llm)
    if image:
        query_result = llava.start(image)
        print("query_result:",query_result)
