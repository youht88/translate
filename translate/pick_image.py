import re
md_filename = "fd5b62ab3a530f6bde73e81c0d413a8c_cn.md"
with open(md_filename,'r') as f:
    text = f.read()
images = re.findall(r"!\[(.*?)\]\((.*?)\)",text)
for image in images:
    print(images)