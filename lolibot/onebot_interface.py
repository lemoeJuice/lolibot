import asyncio
from typing import Dict, Any


class _SequenceGenerator:
    _seq = -1
    _lock = asyncio.Lock()

    @classmethod
    async def next(cls) -> int:
        async with cls._lock:
            cls._seq = (cls._seq + 1) % 2147483647
            return cls._seq + 1  # 不能返回0，不然result存储类的add方法会出问题


class ResultStore:
    _futures: Dict[int, asyncio.Future] = {}

    @classmethod
    def add(cls, result: Dict[str, Any]):
        if seq := result.get('echo'):
            if future := cls._futures.get(seq):
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
            raise Exception(f'API call timeout with timeout_sec {timeout_sec}.')
        finally:
            # don't forget to remove the future object
            del cls._futures[seq]


def _handle_onebot_response(payload):  # 是否需要写成异步
    if 'post_type' in payload:  # event
        asyncio.create_task(_handle_event(payload))
    else:  # api
        asyncio.create_task(_handle_api(payload))


async def _handle_api(payload: Dict[str, Any]):
    print(f'Api: {payload}')
    ResultStore.add(payload)


from .__init__ import _send_wsr


async def call_onebot_api(action_name: str, params: Dict[str, Any], timeout: float = 3):
    seq = await _SequenceGenerator.next()
    await _send_wsr({'action': f'{action_name}', 'params': params, 'echo': seq})
    result = await ResultStore.fetch(seq, timeout)
    print(f'Api result: {result}')
    if result['status'] == 'failed':
        raise Exception(f'Api Action received but failed: {result}')


async def _handle_meta(payload: Dict[str, Any]):
    if payload.get('meta_event_type') == 'heartbeat':
        interval = payload.get('interval')
        status = payload.get('status')
        print(f'Heartbeat detected by interval {interval}ms : {status}')
    elif payload.get('meta_event_type') == 'lifecycle' and payload.get('sub_type') == 'connect':
        await on_wsr_connect()


async def on_wsr_connect():
    print('Bot Client Connected.')


async def _handle_message(payload: Dict[str, Any]):
    print(f'Message: {payload}')


async def _handle_event(payload):
    post_type = payload['post_type']
    if post_type == 'meta_event':
        await _handle_meta(payload)
    elif post_type == 'message':
        await _handle_message(payload)
    else:  # notice（群标识等） & request（加好友加群等）
        pass


async def send_message(is_group: bool, obj_id: int, content: list[Dict[str, Any]]):
    params = {'message_type': 'group', 'group_id': obj_id, 'message': content} if is_group \
        else {'message_type': 'private', 'user_id': obj_id, 'message': content}
    await call_onebot_api('send_msg', params)
