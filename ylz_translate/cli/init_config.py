import os
import shutil

def copy_config():
    current_path = os.path.abspath(__file__)
    config_dir = os.path.dirname(current_path)
    config_file = os.path.join(config_dir,"..","config.yaml")
    dest_dir = os.path.join(os.path.expanduser("~"), ".ylz_translate")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    target_file = os.path.join(dest_dir, config_file)
    if not os.path.exists(target_file):
        shutil.copy(config_file, dest_dir)
    else:
        os.remove(target_file)
        shutil.copy(config_file, dest_dir)

if __name__ == "__main__":
    copy_config()
