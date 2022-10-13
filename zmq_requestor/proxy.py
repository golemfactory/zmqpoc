import aiohttp
import asyncio
from typing import Final, TypeVar, List, Generator

from .service import ZMQService

WEBSOCKET_CHUNK_LIMIT: Final[int] = 2**16
DEFAULT_SOCKET_BUFFER_SIZE: Final[int] = 1024 * 1024
DEFAULT_TIMEOUT: Final[float] = 3000.0

BufferType = TypeVar("BufferType", bytes, memoryview)


def chunks(data: BufferType, chunk_limit) -> Generator[BufferType, None, None]:
    max_chunk, remainder = divmod(len(data), chunk_limit)
    for chunk in range(0, max_chunk + (1 if remainder else 0)):
        yield data[chunk * chunk_limit : (chunk + 1) * chunk_limit]


class ProxyConnection:
    send_reader: asyncio.StreamReader
    send_writer: asyncio.StreamWriter
    ws: aiohttp.ClientWebSocketResponse

    def __init__(
        self,
        proxy: "SocketProxy",
        listen_reader: asyncio.StreamReader,
        listen_writer: asyncio.StreamWriter,
    ):
        self.proxy = proxy
        self.listen_reader = listen_reader
        self.listen_writer = listen_writer

        self.to_data_len = 0
        self.from_data_len = 0
        self.done = False
        self._tasks: List[asyncio.Task] = list()

        self.ws_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.proxy.timeout)
        )

    def _cancel_tasks(self):
        for t in self._tasks:
            t.cancel()

    async def sender(self):
        if self.proxy.verbose:
            print("------ sender start")
        while not self.done:
            try:
                client_data = await self.listen_reader.read(self.proxy.buffer_size)
                if not client_data:
                    self.done = True
                    self._cancel_tasks()
                    break

                if self.proxy.verbose:
                    print(f"client -> {len(client_data)}")
                self.to_data_len += len(client_data)

                for chunk in chunks(memoryview(client_data), WEBSOCKET_CHUNK_LIMIT):
                    if self.proxy.verbose:
                        print(" . . . . . . . . . chunk", len(chunk))
                    await self.ws.send_bytes(chunk)

                if self.proxy.verbose:
                    print(f"{len(client_data)} -> server")
            except asyncio.CancelledError:
                pass

        if self.proxy.verbose:
            print("------ sender done")

    async def responder(self):
        if self.proxy.verbose:
            print("------ responder start")
        while not self.done:
            try:
                server_response = await self.ws.receive(timeout=self.proxy.timeout)
                if server_response.type == aiohttp.WSMsgType.CLOSED:
                    if self.proxy.verbose:
                        print("server -> CLOSED")
                    self.done = True
                    self._cancel_tasks()
                    break

                server_data = server_response.data

                if self.proxy.verbose:
                    print(f"server -> {len(server_data)}")

                self.listen_writer.write(server_data)
                await self.listen_writer.drain()

                if self.proxy.verbose:
                    print(f"{len(server_data)} -> client")

                self.from_data_len += len(server_data)
            except asyncio.CancelledError:
                pass

        if self.proxy.verbose:
            print("------ responder done")

    async def run(self):
        client_addr = self.listen_writer.get_extra_info("peername")
        print("-" * 40)
        print(f"--- client connection from {client_addr}")
        print(f"--- forwarding to {self.proxy.instance_ws}")

        async with self.ws_session.ws_connect(
            self.proxy.instance_ws,
            headers={"Authorization": f"Bearer {self.proxy.app_key}"},
        ) as self.ws:
            self._tasks.extend(
                [
                    asyncio.create_task(self.sender()),
                    asyncio.create_task(self.responder()),
                ]
            )
            try:
                await asyncio.gather(*self._tasks)
            except asyncio.CancelledError:
                pass
        await self.ws_session.close()
        self.close()

    def close(self):
        print(f"--- done.\n-> {self.to_data_len}\n<- {self.from_data_len}")
        self.listen_writer.close()
        print("-" * 40)


class SocketProxy:
    _task: asyncio.Task
    server: asyncio.AbstractServer

    def __init__(
        self,
        service: ZMQService,
        port: int,
        buffer_size: int = DEFAULT_SOCKET_BUFFER_SIZE,
        timeout: float = DEFAULT_TIMEOUT,
        verbose=False,
    ):
        self.service = service
        self.port = port
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.verbose = verbose

        assert service.network_node, "Service must be started on a VPN."

    @property
    def instance_ws(self):
        return self.service.network_node.get_websocket_uri(self.service.remote_port)  # type: ignore[union-attr]  # noqa

    @property
    def app_key(self):
        return (
            self.service.cluster.service_runner._job.engine._api_config.app_key  # type: ignore[union-attr]  # noqa
        )  # noqa

    async def handler(
        self, listen_reader: asyncio.StreamReader, listen_writer: asyncio.StreamWriter
    ):
        connection = ProxyConnection(self, listen_reader, listen_writer)
        await connection.run()

    async def run(self):
        self.server = await asyncio.start_server(self.handler, "*", self.port)

        addrs = ", ".join(str(sock.getsockname()) for sock in self.server.sockets)
        if self.verbose:
            print(f"Proxy listening on {addrs}")

        async def run_server():
            async with self.server:
                await self.server.serve_forever()

        self._task = asyncio.create_task(run_server())

    async def stop(self):
        print("Stopping proxy...")
        self._task.cancel()
        await asyncio.gather(self._task)
        print("Stopped proxy.")
