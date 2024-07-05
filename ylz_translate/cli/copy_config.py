import os
import shutil

def copy_config():
    config_file = "config.yaml"
    dest_dir = os.path.join(os.path.expanduser("~"), ".ylz_translate")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    target_file = os.path.join(dest_dir, config_file)
    if not os.path.exists(target_file):
        shutil.copy(config_file, dest_dir)

if __name__ == "__main__":
    copy_config()
