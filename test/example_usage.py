from typing import Dict, Any

from lolibot import call_onebot_api, handle_event_funcs


# 将函数装饰为事件处理函数
def handle_event(func):
    handle_event_funcs.append(func)
    return func


# 调用onebot接口实现消息发送
async def send_message(is_group: bool, obj_id: int, content: list[Dict[str, Any]]):
    params = {'message_type': 'group', 'group_id': obj_id, 'message': content} if is_group \
        else {'message_type': 'private', 'user_id': obj_id, 'message': content}
    msg_id = (await call_onebot_api('send_msg_async', params, 3))['data']['message_id']
    print(f'Message {msg_id} sent successfully.')
    return msg_id


@handle_event
async def handle_event_custom(payload):
    post_type = payload['post_type']
    if post_type == 'meta_event':
        await Utils.handle_meta(payload)
    elif post_type == 'message':
        await Utils.handle_message(payload)
    else:  # notice（群标识等） & request（加好友加群等）
        pass


class Utils:
    @staticmethod
    async def handle_meta(payload: Dict[str, Any]):
        if payload.get('meta_event_type') == 'heartbeat':
            interval = payload.get('interval')
            status = payload.get('status')
            print(f'Heartbeat detected by interval {interval}ms : {status}')
        elif payload.get('meta_event_type') == 'lifecycle' and payload.get('sub_type') == 'connect':
            await Utils._on_wsr_connect()

    @staticmethod
    async def _on_wsr_connect():
        print('Bot Client Connected.')

    @staticmethod
    async def handle_message(payload: Dict[str, Any]):
        print(f'Message: {payload}')
        # 复读所有群聊消息
        if gid := payload.get('group_id'):
            await send_message(True, gid, payload['message'])
