import sys

try:
    import ujson as json
except ImportError:
    import json

from quart import Quart, websocket


class _SequenceGenerator:
    _seq = 1

    @classmethod
    def next(cls) -> int:
        s = cls._seq
        cls._seq = (cls._seq + 1) % sys.maxsize
        return s


class Message:
    def __init__(self, is_group: bool, obj_id: int, content):
        self.is_group = is_group
        self.id = obj_id
        self.content = content

    def to_json(self) -> dict:
        if self.is_group:
            return {'message_type': 'group', 'group_id': self.id, 'message': self.content}
        else:
            return {'message_type': 'private', 'user_id': self.id, 'message': self.content}

    async def send(self):
        seq = _SequenceGenerator.next()
        await websocket.send(json.dumps({'action': 'send_msg', 'params': self.to_json(), 'echo': {'seq': seq}}))


async def on_wsr_connect():
    pass


async def _handle_meta(payload):
    print(f'Meta Event: {payload}')
    if payload.get('meta_event_type') == 'lifecycle' and payload.get('sub_type') == 'connect':
        await on_wsr_connect()
    # 需要处理心跳事件


async def _handle_message(payload):
    print(f'Message: {payload}')


async def _handle_api(payload):
    print(f'Api: {payload}')


async def _handle_wsr() -> None:
    while True:
        payload = json.loads(await websocket.receive())
        if post_type := payload.get('post_type'):
            if post_type == 'meta_event':
                await _handle_meta(payload)
            elif post_type == 'message':
                await _handle_message(payload)
            else:
                await _handle_api(payload)


class Bot:

    def __init__(self, import_name: str = '', *, server_app_kwargs: dict | None = None):  # python3.10+

        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.add_websocket('/ws', strict_slashes=False, view_func=_handle_wsr)

    def run(self, host: str = '127.0.0.1', port: int = 8080, *args, **kwargs) -> None:
        self._server_app.run(host=host, port=port, *args, **kwargs)
