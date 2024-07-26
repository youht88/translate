import logging
import os
import shutil

def copy_config(args):
    config_name = args.config_name
    project_name = args.project_name
    current_path = os.path.abspath(__file__)
    config_dir = os.path.dirname(current_path)
    config_file = os.path.join(config_dir,"..",config_name)
    dest_dir = os.path.join(os.path.expanduser("~"), f".{project_name}")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    target_file = os.path.join(dest_dir, config_name)
    if not os.path.exists(target_file):
        shutil.copy(config_file, dest_dir)
    else:
        logging.info(f"已存在的{config_name}将被覆盖.")
        os.remove(target_file)
        shutil.copy(config_file, dest_dir)

def reset(args):
    copy_config(args)
