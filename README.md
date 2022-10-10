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
python zmqpoc/plain_server.py
```

### the client

```
python zmqpoc/plain_client.py
```
