''' Starts a BIND9 bindd and handles UDP traffic on port 53 '''

import socket
import threading
import time
import docker

from geolite2 import geolite2
from dns import query

from src.logger import logger
from src.listen_thread import ListenThread
from src import tables
from src import chain
from src.lazy_init import lazy_init

class UDPThread(ListenThread, threading.Thread):
    ''' The thread that gets created in listen_thread. '''
    # pylint: disable=E1101, W0613
    @lazy_init
    def __init__(self, container, database):
        super().__init__(container, database)
        self.container_gateway = self.container_ip = self.container_port = self.container_protocol = None
        self.connection = self.bindd = None
        self.listen_address = self.container.get('listen_address', '')
        self.listen_port = self.container['listen_port']
        self.reader = geolite2.reader()
        self.database = database
        self.shutdown_requested = False

    def _create_socket(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.settimeout(5)

        listen_address = (self.listen_address, self.listen_port)
        logger.info('Listening to %s', str(listen_address))
        listen_socket.bind(listen_address)

        return listen_socket

    def _fetch_container_attributes(self):
        nwsettings = self.bindd.attrs['NetworkSettings']
        self.container_gateway = nwsettings['Networks']['bridge']['Gateway']
        self.container_ip = nwsettings['Networks']['bridge']['IPAddress']

        ports = nwsettings['Ports']
        assert len(ports) == 1

        for port in ports.keys():
            self.container_port = int(port.split('/')[0])
            self.container_protocol = port.split('/')[1]
        logger.debug(self.container_ip)
        logger.debug(self.container_port)
        logger.debug(self.container_protocol)
        chain.create_container_rules(self)

    def _listen_to_queries(self):
        listen_socket = self._create_socket()
        while True:
            try:
                message = query.receive_udp(listen_socket)
                logger.debug('%s read: %s', message[2], str(message[0]))
                self._save_connection(message[2])
                reply = self._send_to_container(message[0])
                self._send_reply(reply, listen_socket, message[2])
                self.database.write(tables.Data(direction='dns', data=message[0].to_wire(), connection=self.connection))
            except socket.timeout:
                if self.shutdown_requested:
                    logger.info('udp_thread shutting down')
                    break
                continue
            except Exception as exc: # pragma: no cover
                logger.debug(exc)
            
        chain.delete_container_rules(self)
        listen_socket.close()

    def _send_to_container(self, message):
        try:
            reply = query.udp(message, self.container_ip, port=self.container_port)
            logger.debug(reply)
        except Exception as exc: # pragma: no cover
            logger.debug(exc)
        return reply

    def _send_reply(self, reply, sock, origin):
        try:
            logger.debug('sending reply to: %s via %s', origin, str(sock))
            r = query.send_udp(sock, reply, origin)
            logger.debug('%s bytes sent to %s', str(r[0]) , origin)
        except Exception as exc: # pragma: no cover
            logger.debug(exc) 

    def run(self):
        chain.create_listen_rules(self)
        try:
            client = docker.from_env()
            self.bindd = client.containers.run(self.container['container'],
                            restart_policy={"Name":"always"}, read_only=True, detach=True)
            logger.info('BINDD container started: %s', self.bindd)
            self.bindd.reload()
            self._fetch_container_attributes()
            self._listen_to_queries()
        except Exception as err: # pragma: no cover
            logger.info(err)

        self._stop_and_remove()

    def _stop_and_remove(self):
        #logger.debug(str(self.bindd.logs()))
        logger.info('Stopping: %s', self.bindd)
        self.bindd.stop()
        logger.info('Removing: %s', self.bindd)
        self.bindd.remove()

    def shutdown(self):
        ''' Called to shutdown the one-way threads and stop and remove the
        container. Called externally in response to a shutdown request. '''
        self.shutdown_requested = True
