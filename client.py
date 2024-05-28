import argparse
import asyncio
from datetime import datetime, timedelta
import json
import os
import random
import sys
from tqdm import tqdm
from typing import Final
import zmq
import zmq.asyncio

from metrics import Metrics

requestor_metrics = Metrics("zmq_requestor")


DEFAULT_ADDRESS: Final = "localhost"
DEFAULT_PORT: Final = 4242
DEFAULT_BUFFER_LEN: Final = 1 * 1024
DEFAULT_MEASUREMENT_TIME: Final = 180

REQUESTOR_WAIT_DELAY: Final = timedelta(seconds=5)
REQUESTOR_WAIT_TIMEOUT: Final = timedelta(minutes=2)

async def wait_for_requestor(quiet: bool, timeout: timedelta = REQUESTOR_WAIT_TIMEOUT):
    start_time = datetime.now()
    while datetime.now() < start_time + timeout:
        requestor_metrics.load()
        status = requestor_metrics["status"]
        if status == "started":
            if not quiet:
                print("Requestor started correctly :)")
            return
        elif status == "failed":
            raise Exception("The requestor has failed.")
        elif status == "terminated":
            raise Exception("The requestor is already terminated.")
        else:
            await asyncio.sleep(REQUESTOR_WAIT_DELAY.total_seconds())

    raise TimeoutError(f"Requestor failed to start within {timeout}")


async def benchmark_comms(
    buffer_len: int, measurement_time: timedelta, quiet: bool, output_json: bool,
):
    report = {
        "success": False,
    }

    try:
        await wait_for_requestor(quiet)
        report["started"] = True
    except Exception as e:
        if not output_json:
            raise

        report["error"] = str(e)
        return report

    last_update = start_time = datetime.now()

    context = zmq.asyncio.Context()

    if not quiet:
        print("Connecting to the zmq server")

    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://localhost:{requestor_metrics['port']}")

    data: bytes = random.randbytes(buffer_len * 1024)

    progress_time = tqdm(total=measurement_time.total_seconds(), unit="s", unit_scale=True, file=open(os.devnull, "w") if quiet else sys.stdout)
    progress_bytes = tqdm(unit="B", unit_scale=True, file=open(os.devnull, "w") if quiet else sys.stdout)

    while datetime.now() - start_time < measurement_time:
        await socket.send(data)
        response = await socket.recv()

        if response == data:
            progress_time.update((datetime.now() - last_update).total_seconds())
            progress_bytes.update(len(data))
            last_update = datetime.now()
            report["elapsed_time"] = progress_time.last_print_n
            report["transmitted_bytes"] = progress_bytes.last_print_n
        else:
            error = f"Transmission failure after {progress_time.last_print_n} seconds / {progress_bytes.last_print_n} bytes"
            if not output_json:
                raise Exception(error)
            else:
                report["error"] = error
                return report

    progress_time.close()
    progress_bytes.close()
    if not quiet:
        print(f"Sent {progress_bytes.last_print_n} bytes in {datetime.now() - start_time}")

    if report["elapsed_time"]:
        report["transmission_speed"] = report["transmitted_bytes"] / report["elapsed_time"]

    return report


parser = argparse.ArgumentParser("ZeroMQ echo client")
parser.add_argument(
    "-l", "--buffer-len",
    type=int,
    default=DEFAULT_BUFFER_LEN,
    help="The length of a single transfer operation in kilobytes, default=%(default)s"
)
parser.add_argument(
    "-t", "--measurement-time",
    type=int,
    default=DEFAULT_MEASUREMENT_TIME,
    help="The time after which to stop sending data in seconds, default=%(default)s")
parser.add_argument(
    "-j", "--output-json",
    action="store_true",
    help="Output JSON metrics, default=%(default)s")
parser.add_argument(
    "-q", "--quiet",
    action="store_true",
    help="Disable regular output and progress info, default=%(default)s")
args = parser.parse_args()

report_output = asyncio.run(
    benchmark_comms(args.buffer_len, timedelta(seconds=args.measurement_time), args.quiet, args.output_json)
)

if args.output_json:
    print(json.dumps(report_output, indent=4))
