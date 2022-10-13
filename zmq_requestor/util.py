import argparse
import asyncio
from colors import yellow
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from yapapi import Golem, __version__ as yapapi_version
from yapapi.log import enable_default_logger


def build_parser(description: str) -> argparse.ArgumentParser:
    current_time_str = utcnow().strftime("%Y%m%d_%H%M%S%z")
    default_log_path = Path(tempfile.gettempdir()) / f"yapapi_{current_time_str}.log"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--payment-driver", "--driver", help="Payment driver name, for example `erc20`"
    )
    parser.add_argument(
        "--payment-network",
        "--network",
        help="Payment network name, for example `rinkeby`",
    )
    parser.add_argument("--subnet-tag", help="Subnet name, for example `devnet-beta`")
    parser.add_argument(
        "--log-file",
        default=str(default_log_path),
        help="Log file for YAPAPI; default: %(default)s",
    )
    return parser


def print_env_info(golem: Golem):
    print(
        f"yapapi version: {yellow(yapapi_version)}\n"
        f"Using subnet: {yellow(golem.subnet_tag)}, "
        f"payment driver: {yellow(golem.payment_driver)}, "
        f"and network: {yellow(golem.payment_network)}\n"
    )


def run_yapapi(example_main, log_file=None):
    if log_file:
        enable_default_logger(
            log_file=log_file,
            debug_activity_api=True,
            debug_market_api=True,
            debug_payment_api=True,
            debug_net_api=True,
        )

    loop = asyncio.get_event_loop()
    task = loop.create_task(example_main)

    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        print(
            yellow(
                "Shutting down gracefully, please wait a short while "
                "or press Ctrl+C to exit immediately..."
            )
        )
        try:
            task.cancel()
            loop.run_until_complete(task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass


def utcnow() -> datetime:
    """Get a timezone-aware datetime for _now_."""
    return datetime.now(tz=timezone.utc)
