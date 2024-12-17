from typing import Dict, Any
import asyncio

try:
    import ujson as json
except ImportError:
    import json

from quart import Quart, websocket


class _SequenceGenerator:
    _seq = -1

    @classmethod
    def next(cls) -> int:
        cls._seq = (cls._seq + 1) % 2147483648
        return cls._seq


class ResultStore:
    _futures: Dict[int, asyncio.Future] = {}

    @classmethod
    def add(cls, result: Dict[str, Any]):
        if isinstance(result.get('echo'), int):
            future = cls._futures.get(result['echo'])
            if future:
                future.set_result(result)

    @classmethod
    async def fetch(cls, seq: int, timeout_sec: float) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[seq] = future
        try:
            return await asyncio.wait_for(future, timeout_sec)
        except asyncio.TimeoutError:
            # haven't received any result until timeout,
            # we consider this API call failed with a network error.
            raise  # NetworkError('WebSocket API call timeout')
        finally:
            # don't forget to remove the future object
            del cls._futures[seq]


class Message:
    def __init__(self, is_group: bool, obj_id: int, content: Dict[str, Any]):
        self.is_group = is_group
        self.id = obj_id
        self.content = content

    def to_json(self) -> dict:
        if self.is_group:
            return {'message_type': 'group', 'group_id': self.id, 'message': self.content}
        else:
            return {'message_type': 'private', 'user_id': self.id, 'message': self.content}

    async def send(self):
        seq: int = _SequenceGenerator.next()
        await websocket.send(json.dumps({'action': 'send_msg', 'params': self.to_json(), 'echo': seq}))


async def on_wsr_connect():
    print('Bot Client Connected.')


async def _handle_meta(payload: Dict[str, Any]):
    # print(f'Meta Event: {payload}')
    if payload.get('meta_event_type') == 'heartbeat':  # 需要处理心跳事件
        interval = payload.get('interval')
        status = payload.get('status')
        print(f'Heartbeat detected by interval {interval}ms : {status}')
    elif payload.get('meta_event_type') == 'lifecycle' and payload.get('sub_type') == 'connect':
        await on_wsr_connect()
    else:
        print(f'Unknown meta_event: {payload}')


async def _handle_message(payload: Dict[str, Any]):
    print(f'Message: {payload}')


async def _handle_api(payload: Dict[str, Any]):
    print(f'Api: {payload}')


async def _handle_wsr() -> None:
    while True:
        payload = json.loads(await websocket.receive())
        if post_type := payload.get('post_type'):
            if post_type == 'meta_event':
                await _handle_meta(payload)
            elif post_type == 'message':
                await _handle_message(payload)
            else:  # 会不会有其他情况
                await _handle_api(payload)


class Bot:

    def __init__(self, import_name: str = '', *, server_app_kwargs: dict | None = None):  # python3.10+

        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.add_websocket('/ws', strict_slashes=False, view_func=_handle_wsr)

    def run(self, host: str = '127.0.0.1', port: int = 8080, *args, **kwargs) -> None:
        self._server_app.run(host=host, port=port, *args, **kwargs)
