# setup
## step1 执行init_config,系统自动将config.yaml文件拷贝到～/.ylz_translate目录下
## step2 根据情况有关环境变量的设置:
### step2.1 LLM
#### export TOGETHER_API_KEYS=<用逗号分隔的together api token>
#### export TOGETHER_LLM_MODEL=<together llm model>  默认为 Qwen/Qwen1.5-72B-Chat

#### export SILICONFLOW_API_KEYS=<用逗号分隔的siliconflow api token>
#### export SILICONFLOW_LLM_MODEL=<siliconflow llm model> 默认为 alibaba/Qwen1.5-110B-Chat

#### export GROQ_API_KEYS=<用逗号分隔的groq api token>
#### export GROQ_LLM_MODEL=<groq llm model> 默认为 llama3-70b-8192

#### export DEEPSEEK_API_KEYS=<用逗号分隔的deepseek api token>
#### export DEEPSEEK_LLM_MODEL=<deepseek llm model>  默认为 deepseek-chat

#### export QIANFAN_API_KEYS=<用逗号分隔的qianfan api token>
#### export QIANFAN_SEC_KEYS=<用逗号分隔的qianfan sec token> 要与QIANFAN_API_KEYS对应
#### export QIANFAN_LLM_MODEL=<qianfan llm model>  默认为 Yi-34B-Chat

### step2.2 EMBEDDING
#### export TOGETHER_EMBEDDING_MODEL=<together embedding model>  默认为 BAAI/bge-large-en-v1.5

### step2.3 SEARCH_TOOL
#### export TAVILY_API_KEYS=<逗号分隔的tavily search api token>  

# run
## ylz_translate -h
