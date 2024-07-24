import asyncio
from ylz_translate.ylz_utils.langchain_utils import *

if __name__ == '__main__':
    Config.init("ylz_translate")
    asyncio.run(main())