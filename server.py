import argparse
import asyncio
from typing import Final
import zmq
import zmq.asyncio

DEFAULT_PORT: Final = 5555


async def run_server(port: int):
    context = zmq.asyncio.Context()

    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{port}")

    while True:
        data = await socket.recv()
        print(".", end="", flush=True)
        await socket.send(data)


parser = argparse.ArgumentParser("ZeroMQ echo server")
parser.add_argument("--port", type=int, default=DEFAULT_PORT)
args = parser.parse_args()

asyncio.run(run_server(port=args.port))
