import argparse
import asyncio
import functools
from typing import Final


DEFAULT_BUFFER_SIZE: Final = 64 * 1024
DEFAULT_SEND_ADDRESS: Final = "localhost"
DEFAULT_SEND_PORT: Final = 5555
DEFAULT_LISTEN_ADDRESS: Final = "*"
DEFAULT_LISTEN_PORT: Final = 6666


async def handler(
    listen_reader: asyncio.StreamReader,
    listen_writer: asyncio.StreamWriter,
    send_address: str,
    send_port: int,
    buffer_size: int,
    verbose: bool,
):
    to_data_len = 0
    from_data_len = 0

    client_addr = listen_writer.get_extra_info("peername")
    print("-" * 40)
    print(f"--- client connection from {client_addr}")

    send_reader, send_writer = await asyncio.open_connection(send_address, send_port)

    server_addr = send_writer.get_extra_info("peername")
    print(f"--- forwarding to {server_addr}")

    done = False

    async def sender():
        nonlocal done, to_data_len
        if verbose:
            print("------ sender start")
        while not done:
            client_data = await listen_reader.read(buffer_size)
            if not client_data:
                done = True
                send_writer.close()
                break

            if verbose:
                print(f"client -> {len(client_data)}")

            to_data_len += len(client_data)

            send_writer.write(client_data)
            await send_writer.drain()

            if verbose:
                print(f"{len(client_data)} -> server")

        if verbose:
            print("------ sender done")

    async def responder():
        nonlocal done, from_data_len
        if verbose:
            print("------ responder start")
        while not done:
            server_data = await send_reader.read(buffer_size)
            if verbose:
                print(f"server -> {len(server_data)}")

            listen_writer.write(server_data)
            await listen_writer.drain()

            if verbose:
                print(f"{len(server_data)} -> client")

            from_data_len += len(server_data)

        if verbose:
            print("------ responder done")

    await asyncio.gather(
        asyncio.create_task(sender()),
        asyncio.create_task(responder()),
    )

    print(f"done.\n-> {to_data_len}\n<- {from_data_len}")
    listen_writer.close()
    send_writer.close()
    print("-" * 40)


async def main(
    listen_address, listen_port, send_address, send_port, buffer_size, verbose
):
    server = await asyncio.start_server(
        functools.partial(
            handler,
            send_address=send_address,
            send_port=send_port,
            buffer_size=buffer_size,
            verbose=verbose,
        ),
        listen_address,
        listen_port,
    )

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


parser = argparse.ArgumentParser("Bi-directional socket forwarder")
parser.add_argument("--listen-address", default=DEFAULT_LISTEN_ADDRESS)
parser.add_argument("--listen-port", type=int, default=DEFAULT_LISTEN_PORT)
parser.add_argument("--send-address", default=DEFAULT_SEND_ADDRESS)
parser.add_argument("--send-port", type=int, default=DEFAULT_SEND_PORT)
parser.add_argument("--buffer-size", type=int, default=DEFAULT_BUFFER_SIZE)
parser.add_argument("--verbose", default=False, action="store_true")
args = parser.parse_args()


asyncio.run(
    main(
        args.listen_address,
        args.listen_port,
        args.send_address,
        args.send_port,
        args.buffer_size,
        args.verbose,
    )
)
