
# Dockerfile used to build the VM image which will be downloaded by providers.
# The file must specify a workdir and at least one volume.

# We're using python slim image in this example to limit the time it takes for the
# resultant image to be first downloaded by providers, given the fact that our example
# here is limited to barebones Python installation.
FROM python:3.9.14-slim

#RUN apt install libzmq3-dev
RUN pip install pyzmq

COPY server.py /golem/run/
WORKDIR /golem/run

EXPOSE 4242/tcp
CMD python server.py --port 4242
