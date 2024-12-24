from quart import Quart, websocket
import asyncio

try:
    import ujson as json  # 速度比python原生json库更快
except ImportError:
    import json


# 为每次api调用生成序列号，以识别返回结果的对应关系
class _SequenceGenerator:
    _seq = -1
    _lock = asyncio.Lock()

    @classmethod
    async def next(cls) -> int:
        async with cls._lock:
            cls._seq = (cls._seq + 1) % 2147483647
            return cls._seq + 1  # 不能返回0，不然result存储类的add方法会出问题


# 存储api返回的结果，以实现异步操作
class _ResultStore:
    _futures = {}

    @classmethod
    def add(cls, result: dict) -> None:
        seq = result.get('echo')
        if future := cls._futures.get(seq):  # python3.8+
            future.set_result(result)

    @classmethod
    async def fetch(cls, seq: int, timeout_sec: float) -> dict:
        future = asyncio.get_event_loop().create_future()
        cls._futures[seq] = future
        try:
            return await asyncio.wait_for(future, timeout_sec)
        finally:
            del cls._futures[seq]


# 向这个列表添加函数，每当收到event推送时列表中的函数将被调用，传入的内容为onebot标准定义的原始内容
handle_event_funcs = []


async def _handle_event(payload: dict) -> None:
    for func in handle_event_funcs:
        await func(payload)


def _handle_onebot_response(payload: dict) -> None:
    if 'post_type' in payload:  # event推送
        asyncio.create_task(_handle_event(payload))
    else:  # api响应
        _ResultStore.add(payload)


# 调用这个函数来使用onebot(v11)接口，接口说明文档可见于https://github.com/botuniverse/onebot-11/
async def call_onebot_api(action_name: str, params: dict, timeout: float):
    seq = await _SequenceGenerator.next()

    # 基于quart的上下文机制，应当能够自动处理ws连接的调用，不会出现多个连接处理串台发送的情况
    # 如果需要标记每个连接，可以通过websocket.headers['X-Self-ID']获取当前连接实现的qq号
    await websocket.send(json.dumps({'action': f'{action_name}', 'params': params, 'echo': seq}))

    # 可以通过自定义异常类型来实现更精确的抛出与捕获，此处仅为示例
    try:
        result = await _ResultStore.fetch(seq, timeout)
    except asyncio.TimeoutError:
        raise Exception(f'API call timeout with timeout_sec {timeout}.')
    if result['status'] == 'failed':
        raise Exception(f'Api call received but failed with message: {result["message"]}')

    return result


# 当有客户端连接时quart框架会自动调用这个函数，目前主流的客户端都是universal形式提供
async def _handle_wsr_conn() -> None:
    role = websocket.headers['X-Client-Role'].lower()
    if role != 'universal':
        raise Exception('当前仅支持universal客户端连接.')

    while True:
        payload = json.loads(await websocket.receive())
        _handle_onebot_response(payload)


# bot类，封装了quart应用提供基于反向ws连接的消息收发功能，创建该类的实例并调用run方法以启动机器人
class Bot:
    # 传入参数为客户端配置的反向ws端点，请务必确认严格匹配（尤其是最后的斜杠），否则可能导致连接问题，可以参考仓库中的测试用例填写
    def __init__(self, server_endpoint, *,
                 import_name: str = __name__, server_app_kwargs: dict | None = None):  # python3.10+
        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.add_websocket(server_endpoint, view_func=_handle_wsr_conn)

    # 传参方式有待改进
    def run(self, host: str = '127.0.0.1', port: int = 8080, *args, **kwargs) -> None:
        if 'debug' not in kwargs:
            kwargs['debug'] = True
        if 'use_reloader' not in kwargs:
            kwargs['use_reloader'] = False
        self._server_app.run(host, port, *args, **kwargs)
