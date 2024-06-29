from logger import logger
import json
import os
import shutil
import glob

class FileLib():
    @classmethod
    def loadJson(cls, filename,encoding='utf8'):
        try:
            with open(filename,"r",encoding=encoding) as f:
                data = json.load(f)
        except Exception as e:
            logger.info(f"{filename} error.")
            data = {}
        return data
    @classmethod
    def dumpJson(cls,filename,data):
        try:
            with open(filename,"w",encoding='utf8') as f:
                json.dump(data,f,ensure_ascii=False,indent=4,sort_keys=True)
            logger.info(f"File saved to {filename}")
        except Exception as e:
            logger.info(f"save {filename} error.")
    @classmethod
    def writeFile(cls,filename,text,mode = "w"):
        # 保存文件
        try:
            if mode.find("b") > -1:
                with open(filename, mode) as f:
                    f.write(text)        
            else:
                with open(filename, mode,encoding="utf8") as f:
                    f.write(text)        
            logger.info(f"File saved to {filename}")
        except Exception as e:
            logger.info(f"save {filename} error.")
    @classmethod
    def readFile(cls,filename,mode = "r"):
        with open(filename,mode,encoding="utf8") as f:
            text = f.read()
        return text
    @classmethod
    def existsFile(cls,filename):
        return os.path.exists(filename)
    @classmethod
    def mkdir(cls,path):
        os.makedirs(path,exist_ok=True)
    @classmethod
    def rmdir(cls,path):
        shutil.rmtree(path,ignore_errors=True)
    @classmethod
    def readFiles(cls,dir,files_glob):
        # 返回文件的内容的字典，key为文件名
        file_contents = {}
        file_names = glob.glob(os.path.join(dir, files_glob))
        file_names.sort()
        for filename in file_names:
            file_contents[filename] = cls.readFile(filename)
        return file_contents
