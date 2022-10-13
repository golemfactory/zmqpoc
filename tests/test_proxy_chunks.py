import random
from zmq_requestor.proxy import chunks

import pytest


@pytest.mark.parametrize(
    "data, chunk_limit, num_expected, mv",
    (
        (random.randbytes(16), 16, 1, True),
        (random.randbytes(8), 16, 1, True),
        (random.randbytes(17), 16, 2, True),
        (random.randbytes(31), 16, 2, True),
        (random.randbytes(256), 16, 16, True),
        (random.randbytes(257), 16, 17, True),
        (random.randbytes(16), 16, 1, False),
        (random.randbytes(8), 16, 1, False),
        (random.randbytes(17), 16, 2, False),
        (random.randbytes(31), 16, 2, False),
        (random.randbytes(256), 16, 16, False),
        (random.randbytes(257), 16, 17, False),
    ),
)
def test_chunks(data, chunk_limit, num_expected, mv):
    num_received = 0
    data_out = b""
    data_in = memoryview(data) if data else data
    for chunk in chunks(data_in, chunk_limit):
        data_out += chunk
        num_received += 1

    assert num_received == num_expected
    assert data_out == data
