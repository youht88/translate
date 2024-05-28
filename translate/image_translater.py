import cv2
import numpy as np
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image,ImageFont,ImageDraw
import matplotlib.pyplot as plt
import os

from utils import *
from langchain_utils import *
import logging

class ImageTranslater():
    def __init__(self,imageFilename="image.json"):
        urllib3_logger = logging.getLogger("urllib3")
        # 设置 urllib3 logger 的级别为 CRITICAL，这样只有严重的错误才会被记录
        urllib3_logger.setLevel(logging.CRITICAL)

        #self.image_url = image_url
        self.chain = self.get_chain()
        self.ocr =  PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)  # 可以根据需要选择语言和是否使用角度分类器
        self.font_path = "./Arial.ttf"
        self.imageFilename = imageFilename
        self.image_task = loadJson(self.imageFilename)
    def get_chain(self):
        # llm = get_chatopenai_llm(
        #     base_url="https://api.together.xyz/v1",
        #     api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
        #     #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
        #     model="meta-llama/Llama-3-8b-chat-hf",
        #     temperature=0.2
        #     )
        llm = get_chatopenai_llm(
            base_url="https://api.together.xyz/v1",
            api_key="398494c6fb9f45648b946fe3aa02c8ba84ac083479e933bb8f7e27eed3fb95f5",
            #api_key="87858a89501682c170edef2f95eabca805b297b4260f3c551eef8521cc69cb87",
            model="Qwen/Qwen1.5-72B-Chat",temperature=0.2)
        systemPromptText = """你是专业的金融技术领域专家,同时也是互联网信息化专家。熟悉蚂蚁金服的各项业务,擅长这些方面的技术文档的翻译。现在将下面的英文文字翻译成中文
            要求
            1.简单明了，任何情况下不要解释原因，只需要翻译原始内容
            2.碰到专有名词、代码、数字、url、程序接口、程序方法名称以及缩写的情况直接输出原始内容
            3.如果不知道如何翻译则直接输出原始内容
            4.要保留原始内容的格式。如1. 、1.1等
        """
        prompt = get_prompt(systemPromptText)
        chain = prompt | llm
        return chain
    def save(self):
        dumpJson(self.imageFilename,self.image_task)
    def start(self,image_url,mode="replace"):
        # mode = 'replace' | 'mark'
        id = md5(image_url)
        if id not in self.image_task:
            self.image_task[id] = {"url":image_url,"mode":mode}
        if os.path.exists(f"img_{id}.png"):
            logger.info(f"img_{id}.png exists")
            return
        image,result =  self.get_ocr(image_url)
        if not image:
            return None
        merged_result = self.merge_adjacent_lines(result)

        if mode == "replace":
            new_image = self.replace_image(id,image,merged_result)
            new_image.save(f"img_{id}.png")
        else:
            new_image = self.mark_image(id,image,merged_result)
            new_image.save(f"img_{id}.png")

        # plt.imshow(new_image)
        # plt.axis('off')
        # plt.show()

    def translate_ocr_text(self,text):
        result = self.chain.invoke(
                {
                    "input": text,
                }
            )
        print(f"{text}-->{result.content}")
        return result.content

    def get_ocr(self, image_url):
        # 加载图像
        #image_url = "https://idocs-assets.marmot-cloud.com/storage/idocs87c36dc8dac653c1/1693280825692-b5bc334d-1898-4142-8e3c-8422cbe43291.png"
        image = get_url_image(image_url)
        if image:
            # 进行OCR识别
            result = self.ocr.ocr(np.array(image), cls=True)
            return (image,result)
        else:
            return (None,None)
    # 合并相邻行文本
    def merge_adjacent_lines(self, result):
        merged_result = []
        for res in result:
            if not res:
                continue
            current_line = list(res[0])
            current_box = np.array(current_line[0])
            has_merged = False
            
            for line in res[1:]:
                # 判断当前行和下一行是否相邻，并且在同一列（通过y坐标和x坐标判断）
                if (abs(current_line[0][3][1] - line[0][0][1]) < 30 and  # 10像素以内认为是相邻行
                    abs(current_line[0][0][0] - line[0][0][0]) < 20):  # 同一列
                    # 合并文本
                    current_line[1] = list(current_line[1])  # 转换为列表
                    current_line[1][0] += ' ' + line[1][0]
                    current_line[1] = tuple(current_line[1])  # 转换回元组

                    # 更新文本框
                    current_box = np.concatenate((current_box, np.array(line[0])))
                    has_merged = True
                else:
                    # 如果发生了合并，则计算合并后的文本框的居中位置
                    if has_merged:
                        min_x = np.min(current_box[:, 0])
                        max_x = np.max(current_box[:, 0])
                        min_y = np.min(current_box[:, 1])
                        max_y = np.max(current_box[:, 1])
                        new_box = np.array([[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]])
                        current_line[0] = new_box.tolist()
                    
                    merged_result.append(tuple(current_line))
                    current_line = list(line)
                    current_box = np.array(current_line[0])
                    has_merged = False

            # 处理最后一行，如果发生了合并，则计算合并后的文本框的居中位置
            if has_merged:
                min_x = np.min(current_box[:, 0])
                max_x = np.max(current_box[:, 0])
                min_y = np.min(current_box[:, 1])
                max_y = np.max(current_box[:, 1])
                new_box = np.array([[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]])
                current_line[0] = new_box.tolist()

            merged_result.append(tuple(current_line))

        # 输出合并后的结果
        for idx in range(len(merged_result)):
            res = merged_result[idx]
            for line in res:
                print(line)

        return [merged_result]

    def replace_image(self, id, image, result):    
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)  # 将PIL图像转换为OpenCV格式
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
                translated_text = self.translate_ocr_text(text)
                # 加载字体
                font = ImageFont.truetype(self.font_path, 20)
                # 在原位置绘制转换后的文字
                draw.text((min_x, min_y), translated_text, fill=(0, 0, 0), font=font)
        # 或显示图像
        # display(inpainted_image_pil)
        return inpainted_image_pil
    def mark_image(self, id, image, result):  
        image = image.convert('RGB')
        # 输出结果
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                print(line) 
        # 可视化结果
        boxes = [line[0] for res in result for line in res]
        txts = [self.translate_ocr_text(line[1][0]) for res in result for line in res]
        scores = [line[1][1] for res in result for line in res]
        im_show = draw_ocr(image, boxes, txts, scores, font_path=self.font_path)
        im_show = Image.fromarray(im_show)
        self.image_task[id]["origin"] = result
        self.image_task[id]["result"] = txts
        return im_show

if __name__ == "__main__":
    image_url = "https://idocs-assets.marmot-cloud.com/storage/idocs87c36dc8dac653c1/1693280825692-b5bc334d-1898-4142-8e3c-8422cbe43291.png"
    image_translater = ImageTranslater()
    image_translater.start(image_url)