from lolibot import Bot
from config import *
import example_usage  # 加载插件内容

bot = Bot(endpoint)
bot.run(host=host, port=port)

# 按如下方式填写config.py:
# host = '127.0.0.1'
# port = 8080
# endpoint = '/ws/'
# 端点填写需要严格匹配

# 根据自己的客户端对应填写，下面是一个例子:
# NapCat1.6.3, onebot11.json:
#   "reverseWs": {
#     "enable": true,
#     "urls": ["ws://127.0.0.1:8080/ws/"]
#   },
# 不同的客户端可能会有默认的endpoint，如OneBot v11的默认端点等，需要自行查找
