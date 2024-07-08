import logging
import os
import shutil

def copy_config():
    file_name = "config.yaml"
    current_path = os.path.abspath(__file__)
    config_dir = os.path.dirname(current_path)
    config_file = os.path.join(config_dir,"..",file_name)
    dest_dir = os.path.join(os.path.expanduser("~"), ".ylz_translate")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    target_file = os.path.join(dest_dir, file_name)
    if not os.path.exists(target_file):
        shutil.copy(config_file, dest_dir)
    else:
        logging.info("已存在的config.yaml将被覆盖.")
        os.remove(target_file)
        shutil.copy(config_file, dest_dir)

if __name__ == "__main__":
    copy_config()
