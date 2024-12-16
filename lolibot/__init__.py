try:
    import ujson as json
except ImportError:
    import json

from quart import Quart, websocket


class Bot:

    def __init__(self, import_name: str = '', *, server_app_kwargs: dict | None = None):  # python3.10+

        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.add_websocket('/', strict_slashes=False, view_func=self._handle_wsr)

    def run(self, host: str = '127.0.0.1', port: int = 8080, *args, **kwargs) -> None:
        self._server_app.run(host=host, port=port, *args, **kwargs)

    async def _handle_wsr(self) -> None:
        while True:
            print(await websocket.receive())