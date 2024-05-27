import hashlib
import requests
from io import BytesIO
from PIL import Image
import base64
import json
from logger import logger

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

def loadJson(filename):
    try:
        with open(filename,"r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"{filename} error.",e)
        data = {}
    return data
def dumpJson(filename,data):
    try:
        with open(filename,"w") as f:
            json.dump(data,f)
    except Exception as e:
        logger.info(f"{filename} error.",e)

def writeFile(filename,text):
    # 保存文件
    with open(filename, "w") as f:
        f.write(text)        
        logger.info(f"File saved to {filename}")
def readFile(filename):
    with open(filename,"r") as f:
        text = f.read()
    return text

def md5(string):
        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()
