from io import BytesIO
import imghdr
from PIL import Image
import base64
import requests
from logger import logger

import xml.etree.ElementTree as ET

def get_url_image(url):
    # 从 URL 下载图片
    response = requests.get(url)
    # 确保请求成功
    if response.status_code == 200:
        # 检查响应头的 Content-Type
        content_type = response.headers.get('Content-Type', '')
        if content_type.startswith('image/'):
            image_type = imghdr.what(None, h=response.content)
            if image_type in ['jpeg', 'jpg', 'bmp', 'png','webp']:
                # 将下载的图片数据转换为字节流
                image_data = BytesIO(response.content)
                # 使用 Pillow 的 Image 模块打开图片
                image = Image.open(image_data)
                # 显示图片
                #display(image)
                return (image,image_type)
            else:
                if content_type.index("svg") > -1:
                    return (response.content, "svg")
                else:
                    logger.debug(f"无法识别图片类型：{image_type}")
                    return (None, None)
    else:
        logger.debug(f"无法下载图片，状态码：{response.status_code}") 
        return (None, None)

def convert_to_base64(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")  # You can change the format if needed
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def indent_svg(elem, level=0):
    """
    Helper function to indent the XML for pretty printing.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent_svg(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i