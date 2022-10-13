# zmqpoc
poc of a zmq communications over yapapi

## prerequisites

### python >= 3.8

### libzmq3

[ not required but recommended ]

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

## running locally

### the server

```
python server.py --port 4242
```

### the forwarder

```
python socket_forwarder.py --listen-port 6767 --send-port 4242
```

### the client

```
python client.py --port 6767
```

## running the server in a docker container

```
docker build -t zmqpoc -f zmqpoc.Dockerfile .
docker run -p 4242:4242 zmqpoc:latest
```

## running on golem

### preparing the GVMI image

```
pip install gvmkit-build
docker build -t zmqpoc -f zmqpoc.Dockerfile .
gvmkit-build zmqpoc:latest
gvmkit-build zmqpoc:latest --push
```

The image is already pushed into the repository under the following hash:

```
3b8b4032194f305aac79d84338851eae46c94cd6efbd02a5009cbfb6
```
