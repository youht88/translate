
import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image,ImageFont,ImageDraw

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import base64
from io import BytesIO
def convert_to_base64(pil_image):
    """
    Convert PIL images to Base64 encoded strings

    :param pil_image: PIL image
    :return: Re-sized Base64 string
    """

    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")  # You can change the format if needed
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str
chat_qwen72b = ChatOpenAI(
        base_url="https://api.together.xyz/v1",
        api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
        #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
        model="Qwen/Qwen1.5-72B-Chat",temperature=0.2)
llm = chat_qwen72b
systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在将下面的英文文字翻译成中文
        要求
        1.简单明了，任何情况下不要解释原因，只需要翻译原始内容
        2.碰到专有名词、代码、数字、url、程序接口、程序方法名称以及缩写的情况直接输出原始内容
        3.如果不需要翻译则直接输出原始内容
        4.要保留原始内容的格式。如1. 、1.1等
    """
prompt = ChatPromptTemplate.from_messages(
    [
        
        (
            "system",
            systemPromptText,
        ),
        ("human", "{input}"),
    ]
)
chain = prompt | llm

def translate(text):
    result = chain.invoke(
            {
                "input": text,
            }
        )
    print(f"{text}-->{result.content}")
    return result.content
# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 可以根据需要选择语言和是否使用角度分类器

# 加载图像
image_path = 'test4.png'
image = Image.open(image_path)
image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)  # 将PIL图像转换为OpenCV格式

# 进行OCR识别
result = ocr.ocr(image_path, cls=True)

########
# # 将结果按照行进行分类和合并
# merged_text = ""
# previous_bottom = None
# line_spacing_threshold = 5  # 根据你的需求调整此阈值

# for line in result[0]:
#     text, box = line[1][0], line[0]
#     top = min(box[0][1], box[1][1], box[2][1], box[3][1])
#     bottom = max(box[0][1], box[1][1], box[2][1], box[3][1])

#     if previous_bottom is not None and (top - previous_bottom) > line_spacing_threshold:
#         merged_text += "\n"

#     merged_text += text
#     previous_bottom = bottom

# print(merged_text)
########

# 创建一个掩码图像，用于标记需要修复的区域
mask = np.zeros(image_cv.shape[:2], dtype=np.uint8)

# 遍历识别结果，标记文字区域
for line in result:
    for word_info in line:
        # 获取文字的边界框
        bbox = word_info[0]
        # 将边界框转换为整数并标记到掩码图像上
        points = np.array(bbox, dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)

# 使用OpenCV的inpaint方法进行背景修复
inpainted_image = cv2.inpaint(image_cv, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

# 将修复后的图像转换回PIL格式
inpainted_image_pil = Image.fromarray(cv2.cvtColor(inpainted_image, cv2.COLOR_BGR2RGB))

# 创建一个绘图对象
draw = ImageDraw.Draw(inpainted_image_pil)

# 字体路径和大小，可以根据需要调整
font_path = "Arial.ttf"
font_size = 20

# 遍历识别结果，替换文字
for line in result:
    for word_info in line:
        # 获取文字的边界框和内容
        bbox, text = word_info[0], word_info[1][0]
        
        # 获取最小和最大坐标
        min_x = min(bbox, key=lambda x: x[0])[0]
        min_y = min(bbox, key=lambda x: x[1])[1]

        # 转换文字（这里可以进行任何你需要的转换，比如更改文字内容、字体、颜色等）
        # 例如：替换为 "替换后的文字"
        translated_text = translate(text)
        
        # 加载字体
        font = ImageFont.truetype(font_path, font_size)
        
        # 在原位置绘制转换后的文字
        draw.text((min_x, min_y), translated_text, fill=(0, 0, 0), font=font)

# 保存或展示结果图像
output_path = 'output_image.jpg'
inpainted_image_pil.save(output_path)

# 或显示图像
inpainted_image_pil.show()