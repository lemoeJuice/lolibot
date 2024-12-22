import asyncio


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


_handle_event_funcs = []


def handle_event(func):
    _handle_event_funcs.append(func)
    return func


async def _handle_event(payload):
    for func in _handle_event_funcs:
        await func(payload)


async def _handle_api(payload):
    _ResultStore.add(payload)


from .__init__ import _send_wsr


async def call_onebot_api(action_name: str, params: dict, timeout: float):
    seq = await _SequenceGenerator.next()
    await _send_wsr({'action': f'{action_name}', 'params': params, 'echo': seq})
    return await _ResultStore.fetch(seq, timeout)
