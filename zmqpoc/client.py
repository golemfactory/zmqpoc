import argparse
import asyncio
from datetime import timedelta
import random
from tqdm import tqdm
from typing import Final
import zmq
import zmq.asyncio


DEFAULT_ADDRESS: Final = "localhost"
DEFAULT_PORT: Final = 5555
DEFAULT_BUFFER_LEN: Final = 1 * 1000 * 1000
DEFAULT_NUM_ITERATIONS: Final = 1000


async def benchmark_comms(
    address: str, port: int, buffer_len: int, num_iterations: int
):
    context = zmq.asyncio.Context()

    print("Connecting to the zmq server")
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{address}:{port}")

    data: bytes = random.randbytes(buffer_len)

    t = tqdm(total=num_iterations * buffer_len, unit="B", unit_scale=True)

    #  Do 10 requests, waiting each time for a response
    for i in range(num_iterations):
        await socket.send(data)
        response = await socket.recv()

        if response == data:
            t.update(buffer_len)
        else:
            raise Exception(f"Transmission failure after {t.last_print_n} bytes")

    t.close()
    print(f"Sent {t.n} bytes in {timedelta(seconds=t.last_print_t - t.start_t)}")


parser = argparse.ArgumentParser("ZeroMQ echo client")
parser.add_argument("--address", default=DEFAULT_ADDRESS)
parser.add_argument("--port", type=int, default=DEFAULT_PORT)
parser.add_argument("--buffer-len", type=int, default=DEFAULT_BUFFER_LEN)
parser.add_argument("--num-iterations", type=int, default=DEFAULT_NUM_ITERATIONS)
args = parser.parse_args()

asyncio.run(
    benchmark_comms(args.address, args.port, args.buffer_len, args.num_iterations)
)
