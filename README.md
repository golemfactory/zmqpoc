# zmqpoc
poc of zmq communications over yapapi and Golem Network

## prerequisites

### python >= 3.9

### libzmq3

[ not required but recommended ]

```bash
sudo apt install libzmq3-dev
```

### yagna daemon

In order to run on Golem, one needs to install the yagna daemon.

Please follow the [requestor's introduction on running tasks on Golem](https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development).

```
curl -ksSf https://join.golem.network/as-requestor | bash -
```

and then, when running yagna, specify:

```
yagna service run
```


## installing

```bash
git clone https://github.com/golemfactory/zmqpoc.git
cd zmqpoc
pip install -U pip poetry
poetry install
```

## running locally (POC of a POC of a POC ;)

### the server

```bash
python server.py --port 4242
```

### the forwarder

```bash
python socket_forwarder.py --listen-port 6767 --send-port 4242
```

### the client

```bash
python client.py --port 6767
```

## running the server in a docker container (POC of a POC)

```bash
docker build -t zmqpoc -f zmqpoc.Dockerfile .
docker run -p 4242:4242 zmqpoc:latest
```

## running on golem (the proper POC0)

### preparing the GVMI image

```bash
pip install gvmkit-build
docker build -t zmqpoc -f zmqpoc.Dockerfile .
gvmkit-build zmqpoc:latest
gvmkit-build zmqpoc:latest --push
```

The image is already pushed into the repository under the following hash:

```
3b8b4032194f305aac79d84338851eae46c94cd6efbd02a5009cbfb6
```

### running the requestor

Make sure your `yagna` is launched and running on the hybrid net and remember about
initializing the payment driver and about adding your application key as 
`YAGNA_APPKEY` to the environment.

Then, launch the requestor as:

```bash
python -m zmq_requestor
```

or, if you wish to see more debug info about the performed connections:

```bash
python -m zmq_requestor --verbose
```

for the full usage, see:

```bash
python -m zmq_requestor --help
```

After the requestor announces that it's listening:

```
ZMQ server started
Listening on local port: 4242
```

you may run the client:

```
python client.py --port 4242 --buffer-len 65536 --num-iterations 100
```
