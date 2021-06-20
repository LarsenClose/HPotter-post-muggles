''' Listen to a socket and create a container thread in response to a
connection. Called from __main__.py. '''

import socket
import threading
import ssl
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor

from OpenSSL import crypto
from geolite2 import geolite2

from src.logger import logger
from src import tables
from src.container_thread import ContainerThread
from src import chain
from src.ssh import SshThread

class ListenThread(threading.Thread):
    ''' Set up the port, listen to it, create a container thread. '''
    def __init__(self, container, database):
        super().__init__()
        self.container = container
        self.database = database
        self.to_rule = None
        self.from_rule = None

        if 'request_save' not in self.container:
            self.container['request_save'] = True
        if 'response_save' not in self.container:
            self.container['response_save'] = False

        self.shutdown_requested = False
        self.TLS = 'TLS' in self.container and self.container['TLS']
        self.context = None
        self.container_list = []
        self.connection = None
        self.listen_address = self.container.get('listen_address', '')
        self.listen_port = self.container['listen_port']
        self.reader = geolite2.reader()

    # https://stackoverflow.com/questions/27164354/create-a-self-signed-x509-certificate-in-python
    def _gen_cert(self):
        if 'key_file' in self.container:
            logger.info('Reading from SSL configuration files')
            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.context.load_cert_chain(self.container['cert_file'], self.container['key_file'])
        else:
            logger.info('Creating SSL configuration files')
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 4096)
            cert = crypto.X509()
            cert.get_subject().C = "UK"
            cert.get_subject().ST = "London"
            cert.get_subject().L = "Diagon Alley"
            cert.get_subject().OU = "The Leaky Caldron"
            cert.get_subject().O = "J.K. Incorporated"
            cert.get_subject().CN = socket.gethostname()
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, 'sha1')

            # can't use an iobyte file for this as load_cert_chain only take a
            # filesystem path :/
            cert_file = tempfile.NamedTemporaryFile(delete=False)
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            cert_file.close()

            key_file = tempfile.NamedTemporaryFile(delete=False)
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
            key_file.close()

            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.context.load_cert_chain(certfile=cert_file.name, keyfile=key_file.name)

            os.remove(cert_file.name)
            os.remove(key_file.name)

    def _save_connection(self, address):
        latitude = None
        longitude = None

        info = self.reader.get(address[0])
        if info and 'location' in info:
            location = info['location']
            if 'latitude' in location and 'longitude' in location:
                latitude = str(location['latitude'])
                longitude = str(location['longitude'])

        if 'save_destination' in self.container:
            self.connection = tables.Connections(
                destination_address = self.listen_address,
                destination_port = self.listen_port,
                source_address = address[0],
                source_port = address[1],
                latitude = latitude,
                longitude = longitude,
                container = self.container['container'],
                protocol = tables.TCP)
        else:
            self.connection = tables.Connections(
                source_address = address[0],
                source_port = address[1],
                latitude = latitude,
                longitude = longitude,
                container = self.container['container'],
                proto = tables.TCP)

        self.database.write(self.connection)

    def _create_listen_socket(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # check for shutdown request every five seconds
        listen_socket.settimeout(5)

        listen_address = (self.listen_address, self.listen_port)
        logger.info('Listening to %s', str(listen_address))
        listen_socket.bind(listen_address)
        return listen_socket

    def run(self):
        if self.TLS:
            self._gen_cert()

        listen_socket = self._create_listen_socket()
        chain.create_listen_rules(self)
        listen_socket.listen()

        num_threads = self.container.get('threads', None)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            while True:
                source = None
                try:
                    source, address = listen_socket.accept()
                    if self.TLS:
                        source = self.context.wrap_socket(source, server_side=True)
                    source.settimeout(self.container.get('connection_timeout', 10))
                    self._save_connection(address)
                except socket.timeout:
                    if self.shutdown_requested:
                        logger.info('listen_thread shutting down')
                        break
                    continue
                except Exception as exc:
                    logger.info(exc)

                thread = ContainerThread(source, self.connection, self.container, self.database) \
                    if self.container['container'] != 'debian:sshd' else \
                         SshThread(source, self.connection, self.container, self.database)

                future = executor.submit(thread.start)
                self.container_list.append((future, thread))

        listen_socket.close()

    def shutdown(self):
        ''' Shut down all the container threads created. Called externally.  '''
        logger.info('listen_thread shutdown called')
        self.shutdown_requested = True
        for (future, container_thread) in self.container_list:
            if future.running():
                container_thread.shutdown()
