import asyncio
import random
from tqdm import tqdm
import zmq
import zmq.asyncio

BUFFER_LEN = 1 * 1000 * 1000
NUM_ITERATIONS = 1000

data: bytes = random.randbytes(BUFFER_LEN)
exchanged_size = 0

context = zmq.asyncio.Context()


async def communicate():
    print("Connecting to the zmq server")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    t = tqdm(total=NUM_ITERATIONS * BUFFER_LEN, unit="B", unit_scale=True)

    #  Do 10 requests, waiting each time for a response
    for i in range(NUM_ITERATIONS):
        await socket.send(data)
        response = await socket.recv()

        if response == data:
            t.update(BUFFER_LEN)
        else:
            raise Exception("transmission failure")

    t.close()


asyncio.run(communicate())
