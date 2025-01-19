该项目使用OneBot v11定义的反向websocket方式与协议端进行通信，与Lagrange/NapCat/LLOnebot等协议端兼容

具体实现参考了[aiocqhttp](https://github.com/nonebot/aiocqhttp)框架的相关内容

### 特点：
- **轻量化&单文件支持**：所有代码包含在一个文件中，仅需通过pip安装Quart框架即可使用
- **高可读性&高扩展性**：只包含最基础的协议封装，调用关系清晰，返回原始api内容，适合初学与二次开发
