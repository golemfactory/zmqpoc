import asyncio
import colors
from datetime import timedelta


from yapapi import Golem
from yapapi.services import Cluster, ServiceState
from yapapi.contrib.service.socket_proxy import SocketProxy

from .service import ZMQService
from .util import build_parser, run_yapapi, print_env_info, utcnow

from metrics import Metrics

STARTING_TIMEOUT = timedelta(minutes=4)


m = Metrics("zmq_requestor", readonly=False)
m.load()
m["status"] = "init"
m.save()

def cluster_starting(cluster: Cluster):
    return any(
        i.state in (ServiceState.pending, ServiceState.starting)
        for i in cluster.instances
    )


async def main(subnet_tag, payment_driver, payment_network, port, verbose):
    async with Golem(
        budget=1.0,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network,
    ) as golem:
        m["status"] = "starting"
        m.save()

        print_env_info(golem)

        network = await golem.create_network("192.168.0.1/24")
        async with network:
            commissioning_time = utcnow()

            cluster = await golem.run_service(
                ZMQService,
                network=network,
            )

            while (
                cluster_starting(cluster)
                and utcnow() < commissioning_time + STARTING_TIMEOUT
            ):
                print(cluster.instances)
                await asyncio.sleep(5)

            if cluster_starting(cluster):
                m["status"] = "failed"
                m.save()

                raise Exception(
                    f"Failed to start {cluster} instances "
                    f"after {STARTING_TIMEOUT.total_seconds()} seconds"
                )

            print(colors.cyan("ZMQ server started"))

            proxy = SocketProxy(ports=[port])
            await proxy.run(cluster)

            print(colors.cyan(f"Listening on local port: {port}"))

            m["status"] = "started"
            m["port"] = port
            m.save()

            # wait until Ctrl-C

            while True:
                print(cluster.instances)
                try:
                    await asyncio.sleep(10)
                except (KeyboardInterrupt, asyncio.CancelledError):
                    break

            # perform the shutdown of the local http server and the service cluster

            m["status"] = "terminated"
            m.save()

            await proxy.stop()
            print(colors.cyan("ZMQ server stopped"))

            cluster.stop()

            cnt = 0
            while cnt < 3 and any(s.is_available for s in cluster.instances):
                print(cluster.instances)
                await asyncio.sleep(5)
                cnt += 1


if __name__ == "__main__":
    parser = build_parser("ZeroMQ example")
    parser.add_argument(
        "--port",
        type=int,
        default=4242,
        help="The local port to listen on",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show debug messages",
    )
    args = parser.parse_args()

    run_yapapi(
        main(
            subnet_tag=args.subnet_tag,
            payment_driver=args.payment_driver,
            payment_network=args.payment_network,
            port=args.port,
            verbose=args.verbose,
        ),
        log_file=args.log_file,
    )
