import argparse
import asyncio
from typing import Final


DEFAULT_BUFFER_SIZE: Final = 64 * 1024
DEFAULT_SEND_ADDRESS: Final = "localhost"
DEFAULT_SEND_PORT: Final = 5555
DEFAULT_LISTEN_ADDRESS: Final = "*"
DEFAULT_LISTEN_PORT: Final = 6666


class Connection:
    send_reader: asyncio.StreamReader
    send_writer: asyncio.StreamWriter

    def __init__(
        self,
        forwarder: "SocketForwarder",
        listen_reader: asyncio.StreamReader,
        listen_writer: asyncio.StreamWriter,
    ):
        self.forwarder = forwarder
        self.listen_reader = listen_reader
        self.listen_writer = listen_writer

        self.to_data_len = 0
        self.from_data_len = 0
        self.done = False

    async def sender(self):
        if self.forwarder.verbose:
            print("------ sender start")
        while not self.done:
            client_data = await self.listen_reader.read(self.forwarder.buffer_size)
            if not client_data:
                self.done = True
                self.send_writer.close()
                break

            if self.forwarder.verbose:
                print(f"client -> {len(client_data)}")

            self.to_data_len += len(client_data)

            self.send_writer.write(client_data)
            await self.send_writer.drain()

            if self.forwarder.verbose:
                print(f"{len(client_data)} -> server")

        if self.forwarder.verbose:
            print("------ sender done")

    async def responder(self):
        if self.forwarder.verbose:
            print("------ responder start")
        while not self.done:
            server_data = await self.send_reader.read(self.forwarder.buffer_size)
            if self.forwarder.verbose:
                print(f"server -> {len(server_data)}")

            self.listen_writer.write(server_data)
            await self.listen_writer.drain()

            if self.forwarder.verbose:
                print(f"{len(server_data)} -> client")

            self.from_data_len += len(server_data)

        if self.forwarder.verbose:
            print("------ responder done")

    async def run(self):
        client_addr = self.listen_writer.get_extra_info("peername")
        print("-" * 40)
        print(f"--- client connection from {client_addr}")

        self.send_reader, self.send_writer = await asyncio.open_connection(
            self.forwarder.send_address, self.forwarder.send_port
        )

        server_addr = self.send_writer.get_extra_info("peername")
        print(f"--- forwarding to {server_addr}")

        await asyncio.gather(
            asyncio.create_task(self.sender()),
            asyncio.create_task(self.responder()),
        )
        self.close()

    def close(self):
        print(f"done.\n-> {self.to_data_len}\n<- {self.from_data_len}")
        self.listen_writer.close()
        self.send_writer.close()
        print("-" * 40)


class SocketForwarder:
    def __init__(
        self,
        listen_address: str,
        listen_port: int,
        send_address: str,
        send_port: int,
        buffer_size: int,
        verbose: bool,
    ):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.send_address = send_address
        self.send_port = send_port
        self.buffer_size = buffer_size
        self.verbose = verbose

    async def handler(
        self, listen_reader: asyncio.StreamReader, listen_writer: asyncio.StreamWriter
    ):
        connection = Connection(self, listen_reader, listen_writer)
        await connection.run()

    async def run(self):
        server = await asyncio.start_server(
            self.handler,
            self.listen_address,
            self.listen_port,
        )

        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")

        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Bi-directional socket forwarder")
    parser.add_argument("--listen-address", default=DEFAULT_LISTEN_ADDRESS)
    parser.add_argument("--listen-port", type=int, default=DEFAULT_LISTEN_PORT)
    parser.add_argument("--send-address", default=DEFAULT_SEND_ADDRESS)
    parser.add_argument("--send-port", type=int, default=DEFAULT_SEND_PORT)
    parser.add_argument("--buffer-size", type=int, default=DEFAULT_BUFFER_SIZE)
    parser.add_argument("--verbose", default=False, action="store_true")
    args = parser.parse_args()

    socket_forwarder = SocketForwarder(
        args.listen_address,
        args.listen_port,
        args.send_address,
        args.send_port,
        args.buffer_size,
        args.verbose,
    )

    asyncio.run(socket_forwarder.run())
