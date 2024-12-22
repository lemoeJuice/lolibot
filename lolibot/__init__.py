from quart import Quart, websocket

try:
    import ujson as json
except ImportError:
    import json

from .onebot_interface import _handle_onebot_response


async def _handle_wsr_conn() -> None:
    role = websocket.headers['X-Client-Role'].lower()
    if role != 'universal':
        raise Exception('当前仅支持universal客户端连接.')
    while True:
        payload = json.loads(await websocket.receive())
        _handle_onebot_response(payload)


async def _send_wsr(payload) -> None:
    await websocket.send(json.dumps(payload))


class Bot:
    def __init__(self, *, import_name: str = __name__, server_app_kwargs: dict | None = None):  # python3.10+
        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.add_websocket('/ws', view_func=_handle_wsr_conn)

    # 传参方式有待改进
    def run(self, host: str = '127.0.0.1', port: int = 8080, *args, **kwargs) -> None:
        if 'debug' not in kwargs:
            kwargs['debug'] = False
        if 'use_reloader' not in kwargs:
            kwargs['use_reloader'] = False
        self._server_app.run(host, port, *args, **kwargs)
