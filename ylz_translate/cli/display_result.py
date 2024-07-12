from html import escape
import logging

from ylz_translate.utils.soup_utils import SoupLib
from ylz_translate.utils.crypto_utils import HashLib
from ylz_translate.utils.file_utils import FileLib

import platform
import subprocess
import os

def displayResult(args):
    mode = args.mode
    
    url_id = args.url_id
    url = args.url
    block_idxes = args.blocks
    no_code = args.nocode

    if not url and not url_id:
        logging.info("必须指定url_id或者url!")
        return
    elif url:
        url_id = HashLib.md5(url)
    
    output_html_path = "temp.html"

    # 读取文件内容
    file_en_contents = FileLib.readFiles(f"temp/{url_id}/{mode}","part_[0-9]*_en.html")
    en_blocks_with_idx = [ (idx,item[1]) for idx,item in enumerate(sorted(file_en_contents.items())) if not block_idxes or idx in block_idxes]   
    file_cn_contents = FileLib.readFiles(f"temp/{url_id}/{mode}","part_[0-9]*_cn.html")
    cn_blocks_with_idx = [ (idx,item[1]) for idx,item in enumerate(sorted(file_cn_contents.items())) if not block_idxes or idx in block_idxes]   

    # 创建合并后的 HTML 文件
    create_combined_html(en_blocks_with_idx, cn_blocks_with_idx, output_html_path,no_code)

    # 打开合并后的 HTML 文件
    open_html_file(output_html_path)

def open_html_file(file_path):
    if not os.path.isfile(file_path):
        logging.info(f"File {file_path} does not exist.")
        return

    system_name = platform.system()
    
    if system_name == "Windows":
        os.startfile(file_path)
    elif system_name == "Darwin":  # macOS
        subprocess.run(["open", file_path])
    elif system_name == "Linux":
        subprocess.run(["xdg-open", file_path])
    else:
        logging.info(f"Unsupported operating system: {system_name}")

def create_combined_html(a_content_with_idx, b_content_with_idx, output_path,no_code = False):
    combined_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>翻译HTML片段对比</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
            }}
            .pair {{
                display: flex;
                width: 100%;
                border-bottom: 1px solid #ccc;
            }}
            .content {{
                flex: 1;
                padding: 10px;
                box-sizing: border-box;
                overflow: auto;
                border-right: 1px solid #ccc;
            }}
            .content:last-child {{
                border-right: none;
            }}
            .original {{
                width: 100%;
                border-bottom: 1px solid #ccc;
                padding: 10px;
                box-sizing: border-box;
                overflow: auto;
            }}
            pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
    """    
    
    for (idx_a, content_a), (idx_b, content_b) in zip(a_content_with_idx, b_content_with_idx):
        combined_html += f"""
        <div class="pair">
            <div class="content ">
                <h3>Index: {idx_a}</h3>
                {content_a}
            </div>
            <div class="content ">
                <h3>Index: {idx_b}</h3>
                {content_b}
            </div>  
        </div>
        """
        if not no_code:
            combined_html += f"""<div class="pair">
                <div class="content ">
                    <pre><strong>Original en of {idx_a}:</strong>\n{escape(SoupLib.html2soup(content_a).prettify())}</pre>
                </div>
                <div class="content ">
                    <pre><strong>Original cn of {idx_b}:</strong>\n{escape(SoupLib.html2soup(content_b).prettify())}</pre>
                </div>
            </div>
            """

    combined_html += """</body>
    </html>
    """

    FileLib.writeFile(output_path,combined_html)

