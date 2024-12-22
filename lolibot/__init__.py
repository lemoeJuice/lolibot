from quart import Quart, websocket
import asyncio

try:
    import ujson as json
except ImportError:
    import json


async def _handle_wsr_conn() -> None:
    role = websocket.headers['X-Client-Role'].lower()
    if role != 'universal':
        raise Exception('当前仅支持universal客户端连接.')

    while True:
        payload = json.loads(await websocket.receive())
        _handle_onebot_response(payload)


# 基于quart的上下文机制，应当能够自动处理ws连接的调用，不会出现多个连接处理串台发送的情况
# 如果需要标记每个ws连接，可以通过websocket.headers['X-Self-ID']获取当前连接实现的qq号
async def _send_wsr(payload) -> None:
    await websocket.send(json.dumps(payload))


class _SequenceGenerator:
    _seq = -1
    _lock = asyncio.Lock()

    @classmethod
    async def next(cls) -> int:
        async with cls._lock:
            cls._seq = (cls._seq + 1) % 2147483647
            return cls._seq + 1  # 不能返回0，不然result存储类的add方法会出问题


class _ResultStore:
    _futures = {}

    @classmethod
    def add(cls, result):
        if seq := result.get('echo'):
            if future := cls._futures.get(seq):
                future.set_result(result)

    @classmethod
    async def fetch(cls, seq: int, timeout_sec: float):
        future = asyncio.get_event_loop().create_future()
        cls._futures[seq] = future

        try:
            result = await asyncio.wait_for(future, timeout_sec)
        except asyncio.TimeoutError:
            raise Exception(f'API call timeout with timeout_sec {timeout_sec}.')
        finally:
            del cls._futures[seq]

        if result['status'] == 'failed':
            raise Exception(f'Api call received but failed: {result}')
        return result


def _handle_onebot_response(payload):  # 是否需要写成异步
    if 'post_type' in payload:  # event
        asyncio.create_task(_handle_event(payload))
    else:  # api
        asyncio.create_task(_handle_api(payload))


handle_event_funcs = []


async def _handle_event(payload):
    for func in handle_event_funcs:
        await func(payload)


async def _handle_api(payload):
    _ResultStore.add(payload)


async def call_onebot_api(action_name: str, params: dict, timeout: float):
    seq = await _SequenceGenerator.next()
    await _send_wsr({'action': f'{action_name}', 'params': params, 'echo': seq})
    return await _ResultStore.fetch(seq, timeout)


class Bot:
    def __init__(self, *, import_name: str = __name__, server_app_kwargs: dict | None = None):  # python3.10+
        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.add_websocket('/ws/', view_func=_handle_wsr_conn)  # 需要严格匹配

    # 传参方式有待改进
    def run(self, host: str = '127.0.0.1', port: int = 8080, *args, **kwargs) -> None:
        if 'debug' not in kwargs:
            kwargs['debug'] = True
        if 'use_reloader' not in kwargs:
            kwargs['use_reloader'] = False
        self._server_app.run(host, port, *args, **kwargs)
