import asyncio
import colors
from typing import Final

from yapapi.payload import vm
from yapapi.contrib.service.socket_proxy import SocketProxyService

IMAGE_HASH: Final = "3b8b4032194f305aac79d84338851eae46c94cd6efbd02a5009cbfb6"


class ZMQService(SocketProxyService):
    def __init__(self, remote_port: int = 4242):
        super().__init__()
        self.remote_ports = [remote_port]

    @staticmethod
    async def get_payload():
        return await vm.repo(
            image_hash=IMAGE_HASH,
            capabilities=[vm.VM_CAPS_VPN],  # type: ignore
        )

    async def start(self):
        # perform the initialization of the Service
        # (which includes sending the network details within the `deploy` command)
        async for script in super().start():
            yield script

        assert self._ctx
        script = self._ctx.new_script()

        script.run(
            "/bin/bash",
            "-c",
            f"cd /golem/run && python server.py "
            f"--port {self.remote_ports[0]} > out 2> err &",
        )
        yield script
