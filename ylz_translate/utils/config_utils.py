import os

from .file_utils import FileLib

class ConfigObject:
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigObject(value))
            else:
                setattr(self, key, value)
    def get(self, key_string, default=None):
        """
        支持使用 'key1.subkey1' 形式的字符串获取嵌套值。
        """
        keys = key_string.split('.')
        value = self
        for key in keys:
            if hasattr(value,key):
                value = getattr(value, key)
                if isinstance(value, ConfigObject):
                    continue
                else:
                    break
            else:
                return default
        if value:
            return value
        else:
            return default
            
class Config:
  __config: ConfigObject = None
  @classmethod
  def init(cls, project_name, config_path=None):
    """
    初始化配置。

    Args:
      config_path: 可选，配置文件路径。如果未提供，则首先从本地找config.yaml，其次从用户根目录的.project_name查找
    """
    try:
        if config_path is None:
            if FileLib.existsFile("config.yaml"):
               config_path = "config.yaml"
            else:    
              home = os.path.expanduser("~")
              #project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
              config_path = os.path.join(home, f'.{project_name}', 'config.yaml')
        cls.__config = ConfigObject(FileLib.loadYaml(config_path))
    except:
        raise Exception(f"请将config.yaml配置文件拷贝到当前目录或{home}/.{project_name}下,也可以通过--env参数指定正确的config.yaml文件位置")
  @classmethod
  def get(cls, key=None, default=None):
    # ex. config = Config('project_name')
    #     config.get()
    #     config.get("LLM")
    #     config.get("LLM.TOGETHER.API_KEY","abcd")
    if cls.__config == None:
       raise Exception("请先调用Config.init(project_name,env_file)进行初始化!!")
    if key is None:
        return cls.__config
    else:
        value = cls.__config.get(key, default)
        print("get:",type(value),key,value)
