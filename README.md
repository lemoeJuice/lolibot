该项目的实现参考了aiocqhttp（https://github.com/nonebot/aiocqhttp）
特点：
*轻量&单文件支持：所有代码包含在一个文件中，仅需通过pip安装Quart框架即可使用
*可读性强&封装简单：只包含最基础的协议封装，调用关系清晰，返回原始api内容，适合初学与二次开发
*兼容性强：使用OneBot v11定义的反向websocket方式与客户端进行通信，方便迁移
