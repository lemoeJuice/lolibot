from typing import Dict, Any
import asyncio
import json
from quart import Quart, websocket


class ResultStore:
    _futures: Dict[int, asyncio.Future] = {}

    @classmethod
    def add(cls):
        if future := cls._futures.get(0):
            future.set_result('result')

    @classmethod
    async def fetch(cls) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[0] = future
        try:
            return await asyncio.wait_for(future, 1)
        finally:
            del cls._futures[0]


async def send_message():
    payload = {'action': 'send_msg', 'params': {'message_type': 'group', 'group_id': 0,
                                                'message': [{'type': 'text', 'data': {'text': '收到123.'}}]}}
    await websocket.send(json.dumps(payload))
    print(f'res: {await ResultStore.fetch()}')


async def _handle_wsr() -> None:
    while True:
        payload = json.loads(await websocket.receive())
        if post_type := payload.get('post_type'):
            if post_type == 'message':
                if '123' in payload.get('raw_message'):
                    asyncio.create_task(send_message())
        else:
            print(f'Api: {payload}')
            ResultStore.add()


class Bot:
    def __init__(self):
        self._server_app = Quart('')
        self._server_app.add_websocket('/ws', strict_slashes=False, view_func=_handle_wsr)

    def run(self, host, port) -> None:
        self._server_app.run(host=host, port=port)


Bot().run(host='10.210.72.33', port=8080)
