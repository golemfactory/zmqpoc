import argparse
import asyncio
from datetime import datetime, timedelta
import random
from tqdm import tqdm
from typing import Final
import zmq
import zmq.asyncio

from metrics import Metrics

requestor_metrics = Metrics("zmq_requestor")


DEFAULT_ADDRESS: Final = "localhost"
DEFAULT_PORT: Final = 4242
DEFAULT_BUFFER_LEN: Final = 1 * 1000 * 1000
DEFAULT_MEASUREMENT_TIME: Final = 180
REQUESTOR_WAIT_DELAY: int = 5


async def wait_for_requestor():
    while True:
        requestor_metrics.load()
        status = requestor_metrics["status"]
        if status == "started":
            print("Requestor started correctly :)")
            break
        elif status == "failed":
            raise Exception("The requestor has failed.")
        elif status == "terminated":
            raise Exception("The requestor is already terminated.")
        else:
            await asyncio.sleep(REQUESTOR_WAIT_DELAY)


async def benchmark_comms(
    buffer_len: int, measurement_time: timedelta,
):
    await wait_for_requestor()

    last_update = start_time = datetime.now()

    context = zmq.asyncio.Context()

    print("Connecting to the zmq server")
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://localhost:{requestor_metrics['port']}")

    data: bytes = random.randbytes(buffer_len)

    progress_time = tqdm(total=measurement_time.total_seconds(), unit="s", unit_scale=True)
    progress_bytes = tqdm(unit="B", unit_scale=True)

    #  Do 10 requests, waiting each time for a response
    while datetime.now() - start_time < measurement_time:
        await socket.send(data)
        response = await socket.recv()

        if response == data:
            progress_time.update((datetime.now() - last_update).total_seconds())
            progress_bytes.update(buffer_len)
            last_update = datetime.now()
        else:
            raise Exception(f"Transmission failure after {progress_time.last_print_n} seconds / {progress_bytes.last_print_n} bytes")

    progress_time.close()
    progress_bytes.close()
    print(f"Sent {progress_bytes.last_print_n} bytes in {datetime.now() - start_time}")


parser = argparse.ArgumentParser("ZeroMQ echo client")
parser.add_argument("--buffer-len", type=int, default=DEFAULT_BUFFER_LEN)
parser.add_argument("--measurement-time", type=int, default=DEFAULT_MEASUREMENT_TIME)
args = parser.parse_args()

asyncio.run(
    benchmark_comms(args.buffer_len, timedelta(seconds=args.measurement_time))
)
