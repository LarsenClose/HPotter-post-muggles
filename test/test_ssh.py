from socket import timeout
import unittest
import warnings
from unittest.mock import call, patch

from src.ssh import SSHServer
from src.ssh import SshThread
from src import chain

import docker
import socket
import threading
import time
import paramiko

class TestSSH(unittest.TestCase):

    def setup(self):
        warnings.simplefilter('ignore', category=ResourceWarning)

    def test_ssh(self):
        container = {'container': 'debian:sshd', 'listen_address': '0.0.0.0', 'listen_port': 2020, 'request_length': 4096, 'request_commands': 14, 'request_delimiters': ['\\r\\n'], 'threads': 2}
        connection = unittest.mock.Mock()
        database = unittest.mock.Mock()

        source, dest = socket.socketpair()

        ssh = SshThread(dest, connection, container, database)
        ssh.start()

        transport = paramiko.Transport(source)
        transport.connect(username='root', password='toor')
        transport.open_session()

        time.sleep(3)

        self.assertEqual(ssh.connection, connection)
        self.assertEqual(ssh.database, database)
        self.assertEqual(ssh.container_config, container)
        self.assertEqual(ssh.user, 'root')
        self.assertEqual(ssh.password, 'toor')

        source.close()
        dest.close()
        transport.close()

        ssh.join()