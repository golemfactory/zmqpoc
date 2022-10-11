import asyncio

DEFAULT_BUFFER_SIZE = 64 * 1024
DEFAULT_SEND_ADDRESS = "localhost"
DEFAULT_SEND_PORT = 5555
DEFAULT_LISTEN_ADDRESS = "*"
DEFAULT_LISTEN_PORT = 6666


async def handler(
    listen_reader: asyncio.StreamReader, listen_writer: asyncio.StreamWriter
):
    client_addr = listen_writer.get_extra_info("peername")
    print("-" * 40)
    print(f"--- client connection from {client_addr}")

    send_reader, send_writer = await asyncio.open_connection(
        DEFAULT_SEND_ADDRESS, DEFAULT_SEND_PORT
    )

    server_addr = send_writer.get_extra_info("peername")
    print(f"--- forwarding to {server_addr}")

    done = False

    async def sender():
        print("------ sender start")
        nonlocal done
        while not done:
            client_data = await listen_reader.read(DEFAULT_BUFFER_SIZE)
            if not client_data:
                done = True
                send_writer.close()
                break

            print(f"client -> {len(client_data)}")

            send_writer.write(client_data)
            await send_writer.drain()

            print(f"{len(client_data)} -> server")

        print("------ sender done")

    async def responder():
        print("------ responder start")
        nonlocal done
        while not done:
            server_data = await send_reader.read(DEFAULT_BUFFER_SIZE)
            print(f"server -> {len(server_data)}")

            listen_writer.write(server_data)
            await listen_writer.drain()

            print(f"{len(server_data)} -> client")

        print("------ responder done")

    await asyncio.gather(
        asyncio.create_task(sender()),
        asyncio.create_task(responder()),
    )

    print("closing connections")
    listen_writer.close()
    send_writer.close()
    print("-" * 40)


async def main():
    server = await asyncio.start_server(
        handler, DEFAULT_LISTEN_ADDRESS, DEFAULT_LISTEN_PORT
    )

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
