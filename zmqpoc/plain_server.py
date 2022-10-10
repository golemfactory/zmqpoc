import asyncio
import zmq
import zmq.asyncio


context = zmq.asyncio.Context()


async def run_server():
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        data = await socket.recv()
        print(".", end="", flush=True)
        await socket.send(data)


asyncio.run(run_server())
