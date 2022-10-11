# zmqpoc
poc of a zmq communications over yapapi

## prerequisites

```

sudo apt install libzmq3-dev

```

## installing

```

git clone https://github.com/golemfactory/zmqpoc.git
cd zmqpoc
pip install -U pip poetry
poetry install

```

## running

### the server

```
python zmqpoc/server.py --port 4242
```

### the forwarder

```
python zmqpoc/socket_forwarder.py --listen-port 6767 --send-port 4242
```

### the client

```
python zmqpoc/client.py --port 6767
```
