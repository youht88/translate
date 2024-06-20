from logger import logger
import json

class FileLib():
    @classmethod
    def loadJson(cls, filename):
        try:
            with open(filename,"r",encoding='utf8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"{filename} error.")
            data = {}
        return data
    @classmethod
    def dumpJson(cls,filename,data):
        try:
            with open(filename,"w",encoding='utf8') as f:
                json.dump(data,f,ensure_ascii=False,indent=4,sort_keys=True)
        except Exception as e:
            logger.info(f"{filename} error.")
    @classmethod
    def writeFile(cls,filename,text,mode = "w"):
        # 保存文件
        if mode.find("b") > -1:
            with open(filename, mode) as f:
                f.write(text)        
        else:
            with open(filename, mode,encoding="utf8") as f:
                f.write(text)        
        logger.info(f"File saved to {filename}")
    @classmethod
    def readFile(cls,filename,mode = "r"):
        with open(filename,mode,encoding="utf8") as f:
            text = f.read()
        return text