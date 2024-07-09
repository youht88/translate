
import logging
import argparse

from ylz_translate.cli.init import init

from ylz_translate.cli.start import start
from ylz_translate.cli.clear_task import clearTask
from ylz_translate.cli.fix_dict import fixDict
from ylz_translate.cli.sync_dict import syncDict

def main():
    parser = argparse.ArgumentParser(description = "渐进式翻译系统")
    parser.add_argument("--mode", required=True, choices=["markdown","html","json"],help="操作模式(markdown|html|json)")
    parser.add_argument("--log_level",type=str,default="INFO",choices=["INFO","DEBUG"],help="日志级别,默认:INFO")
    parser.add_argument("--log",type=str,default="task.log",help="日志文件名称")
    parser.add_argument("--env_file",type=str,required=False,help="配置文件名称")
    
    subparsers = parser.add_subparsers(dest="command", help="可以使用的子命令")

    start_parser = subparsers.add_parser("start", help="启动翻译")
    start_parser.add_argument("--url",type=str,help="url地址,如果不指定则从--url_file文件获取")
    start_parser.add_argument("-f","--url_file",type=str,help="包含一行或多行url的文件,指定url时忽略此参数")
    start_parser.add_argument("--crawl",type=int,default=0,choices=[0,1,2,3],help="爬取网页的层级深度,默认:0,表示仅当前网页")
    start_parser.add_argument("--only_download",type=bool,default=False,help="仅下载网页html,不进行翻译。默认:False (json模式该参数不起作用)")
    start_parser.add_argument("-s","--size",type=int,default=1500,help="切分文件的字节大小,默认:1500")
    start_parser.add_argument("-c","--clear_error",action="store_true",help="清除task.json文件中的错误信息,默认:False")

    fixDict_parser = subparsers.add_parser("fixDict", help="根据hash或文本特征更新相应字典，以便渐进式翻译")
    fixDict_parser.add_argument("--dict_hash", required=False, help="字典的hash值(6位)")
    fixDict_parser.add_argument("--issubtext", action="store_true",required=False, help="是否是部分文字片段")
    fixDict_parser.add_argument("--old_text",required=False,help="限定字典中目标文本或者所包含的文字片段正则表达式，这取决于--issubtext。注意：如果是文字片段正则表达式则应有足够的特征以避免大范围错误更新")
    fixDict_parser.add_argument("--new_text",required=False,help="如果指定字典的hash且--issubtext不为True，则--new_text应为完整的文本；如果指定--old_text，则--new_text指所对应的文字，这取决于--issubtext")
    fixDict_parser.add_argument("-l","--only_list", action="store_true",required=False, help="仅查看，不更改字典和删除文件")
    fixDict_parser.add_argument("--url_ids", nargs="*",type=str, help="限定字典ref包含url_id的列表内容")
    fixDict_parser.add_argument("--origin_text_pattern", type=str,required=False, help="限定字典中原文本片段的正则表达式")
 
    syncDict_parser = subparsers.add_parser("syncDict", help="同步字典")
    syncDict_parser.add_argument("--url_id",help="任务的url id值(32位)")
    syncDict_parser.add_argument("--url", help="任务的url,如果同时指定了--ulr_id则忽略此参数")
    syncDict_parser.add_argument("-f","--url_file",type=str,help="包含一行或多行url的文件,指定--url或--url_id时忽略此参数")
    syncDict_parser.add_argument("--dict_hash", help="字典的hash值(6位)")
    syncDict_parser.add_argument("--clear_step4", action="store_true",required=False, help="清除字典中无用的key")
    
    clearTask_parser = subparsers.add_parser("clearTask", help="清除已完成的翻译,以便重新翻译")
    clearTask_parser.add_argument("--url_id",help="任务的url id值(32位)")
    clearTask_parser.add_argument("--url", help="任务的url,如果同时指定了--ulr_id则忽略此参数")
    clearTask_parser.add_argument("-f","--url_file",type=str,help="包含一行或多行url的文件,指定--url或--url_id时忽略此参数")
    clearTask_parser.add_argument("--blocks",nargs="*",type=int,help="要删除的block index列表,如--blocks 1 3 5")
    clearTask_parser.add_argument("--only_final", action="store_true", default = False,help="仅删除最终的结果文件")
    clearTask_parser.add_argument("--deep_clear", action="store_true", default = False,help="深度删除字典，当字典ref为空时也删除字典key")

    args = parser.parse_args()
    logging.info(str(args))
    
    init(args)

    if args.command == "start":
        start(args)
    elif args.command == "fixDict":    
        fixDict(args)
    elif args.command == "syncDict":
        syncDict(args)
    elif args.command == "clearTask":
        clearTask(args) 

# python3 ../../fix.py --mode json fixDict --dict_hash b614b4 --new_text="一条消息由消息头和消息体组成。以下部分专注于消息体结构。有关消息头结 构，请参阅："
# python3 ../../fix.py --mode json fixDict --old_text "abcde" --new_text="ABCDE"
# python3 ../../fix.py --mode json clearTask --url_id d2a41fe3fc36fe7e998e88623d2889a8 --blocks 1 3 5
# python3 ../../fix.py --mode json fixDict --old_text "<.+>(.*消息由.*?)</.+>" --new_text "报文由报文头和报文正文组成。以下部 分专注于报文正文结构。报文头结构请参阅" --issubtext
# python3 ../../fix.py --mode json fixDict --old_text "<.+>(.*0s.*?)</.+>" --new_text "" --issubtext -l
