import os
import yaml

class Config:
  """
  封装配置信息的类。
  """
  def __init__(self, config_path=None):
    """
    初始化配置。

    Args:
      config_path: 可选，配置文件路径。如果未提供，则使用默认路径。
    """
    if config_path is None:
      project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      config_path = os.path.join(project_root, 'env', 'config.yaml')
    with open(config_path, 'r') as f:
      self._config = yaml.safe_load(f)

  def get(self, key, default=None):
    """
    获取配置值。

    Args:
      key: 配置键。
      default: 可选，默认值。

    Returns:
      配置值，如果键不存在则返回默认值。
    """
    return self._config.get(key, default)

