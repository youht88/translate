import os
import yaml
import logging

class Config:
  _config = None
  @classmethod
  def init(cls, project_name, config_path=None):
    """
    初始化配置。

    Args:
      config_path: 可选，配置文件路径。如果未提供，则使用默认路径。
    """
    try:
        if config_path is None:
            home = os.path.expanduser("~")
            #project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(home, f'.{project_name}', 'config.yaml')
        with open(config_path, 'r') as f:
            cls._config = yaml.safe_load(f)
    except:
        raise Exception(f"请将config.yaml配置文件拷贝到{home}/.{project_name}下,或指定正确的config.yaml文件位置")
  @classmethod      
  def get(cls, key=None, default=None):
    """
    获取配置值。

    Args:
      key: 配置键,为空则返回整个_config。
      default: 可选，默认值。

    Returns:
      配置值，如果键不存在则返回默认值。
    """
    if cls._config == None:
       raise Exception("请先调用Config.init(project_name,env_file)进行初始化!!")
    if key is None:
        return cls._config
    else:
        return cls._config.get(key, default)

