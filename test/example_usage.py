from typing import Dict, Any

from lolibot.onebot_interface import call_onebot_api, handle_event


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
    # 复读所有群聊消息
    if gid := payload.get('group_id'):
        await send_message(True, gid, payload['message'])


@handle_event
async def _handle_event_custom(payload):
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
    msg_id = (await call_onebot_api('send_msg', params, 3))['data']['message_id']
    print(f'msg {msg_id} sent successfully.')
    return msg_id
