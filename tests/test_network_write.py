"""Writes to a printer over the network backend.

A printer whose receive buffer is full accepts a label a little at a time,
while printing frees space. The network backend must keep sending while the
printer accepts data, and must not use sendall(), whose timeout is a deadline
for the whole call rather than a limit on the time between accepted data.

Run with: python -m unittest discover tests
"""

import unittest

from brother_ql.backends.network import BrotherQLBackendNetwork


class TrickleSocket:
    """A socket that accepts at most `chunk` bytes per send() call"""

    def __init__(self, chunk):
        self.chunk = chunk
        self.received = bytearray()
        self.timeouts = []
        self.send_calls = 0

    def settimeout(self, value):
        self.timeouts.append(value)

    def send(self, data):
        self.send_calls += 1
        accepted = bytes(data[:self.chunk])
        self.received += accepted
        return len(accepted)

    def sendall(self, data):
        raise AssertionError("sendall() applies one deadline to the whole label")


def backend_with(sock):
    """Return a network backend that writes to `sock`, without connecting"""
    backend = BrotherQLBackendNetwork.__new__(BrotherQLBackendNetwork)
    backend.read_timeout = 0.01
    backend.write_timeout = 60
    backend.s = sock
    return backend


class TestNetworkWrite(unittest.TestCase):

    def test_slow_printer_receives_the_whole_label(self):
        label = bytes(range(256)) * 300
        sock = TrickleSocket(chunk=1000)
        backend_with(sock)._write(label)
        self.assertEqual(bytes(sock.received), label)
        self.assertEqual(sock.send_calls, -(-len(label) // 1000))

    def test_write_timeout_applies_while_sending(self):
        sock = TrickleSocket(chunk=7)
        backend_with(sock)._write(b"x" * 50)
        # The write timeout covers each send() call, and the read timeout is
        # restored for the next read.
        self.assertEqual(sock.timeouts, [60, 0.01])


if __name__ == "__main__":
    unittest.main()
