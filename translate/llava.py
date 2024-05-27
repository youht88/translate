from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from PIL import Image
import requests
from io import BytesIO
from IPython.display import HTML, display
import base64

def get_url_image(url):
    # 从 URL 下载图片
    response = requests.get(url)
    # 确保请求成功
    if response.status_code == 200:
        # 将下载的图片数据转换为字节流
        image_data = BytesIO(response.content)

        # 使用 Pillow 的 Image 模块打开图片
        image = Image.open(image_data)

        # 显示图片
        #display(image)
        return image
    else:
        print("无法下载图片，状态码：", response.status_code) 
def convert_to_base64(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")  # You can change the format if needed
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

llm = Ollama(model="llava:34b", base_url="http://youht.cc:18034", temperature=0)
url = "https://idocs-assets.marmot-cloud.com/storage/idocs87c36dc8dac653c1/1693280802335-b70b74e9-8236-41e9-8d97-76caac1acfe3.png"
image  = get_url_image(url)
image_b64 = convert_to_base64(image)

llm_with_image_context = llm.bind(images=[image_b64])
#query_chain = llm_with_image_context.invoke("你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在请把这张图原原本本的英文文字找出来")
query_chain = llm_with_image_context.invoke("请输出这张图片的类型,仅包括以下分类：架构图、流程图、UML图、ER图、时序图、用例图、界面图、截图、表格、公式、源代码、其他")

print(query_chain)