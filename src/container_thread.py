''' Starts a container and connects two one-way threads to it. Called from
a listening thread. '''

import socket
import threading
import time
import docker

from src.logger import logger
from src.one_way_thread import OneWayThread
from src.lazy_init import lazy_init
from src import chain

class ContainerThread(threading.Thread):
    ''' The thread that gets created in listen_thread. '''
    # pylint: disable=E1101, W0613
    @lazy_init
    def __init__(self, source, connection, container_config, database):
        super().__init__()
        self.container_ip = self.container_port = self.container_protocol = None
        self.dest = self.thread1 = self.thread2 = self.container = None

    '''
    Need to make a different one for macos as docker desktop for macos
    doesn't allow connecting to a docker-defined network. I'm thinking of
    using 127.0.0.1 and mapping the internal port to one in the range
    25000-25999 as those don't appear to be claimed in
    https://support.apple.com/en-us/HT202944
    I believe client sockets start in the 40000's
    '''
    def _connect_to_container(self):
        nwsettings = self.container.attrs['NetworkSettings']
        self.container_gateway = nwsettings['Networks']['bridge']['Gateway']
        self.container_ip = nwsettings['Networks']['bridge']['IPAddress']
        logger.debug(self.container_ip)

        ports = nwsettings['Ports']
        assert len(ports) == 1

        for port in ports.keys():
            self.container_port = int(port.split('/')[0])
            self.container_protocol = port.split('/')[1]
        logger.debug(self.container_port)
        logger.debug(self.container_protocol)

        chain.create_container_rules(self)

        for _ in range(9):
            try:
                self.dest = socket.create_connection( \
                    (self.container_ip, self.container_port), timeout=2)
                self.dest.settimeout(self.container_config.get('connection_timeout', 10))
                logger.debug(self.dest)
                return
            except Exception as err:
                logger.debug(err)
                time.sleep(2)

        logger.info('Unable to connect to ' + self.container_ip + ':' + \
            str(self.container_port))


    def _start_and_join_threads(self):
        logger.debug('Starting thread1')
        self.thread1 = OneWayThread(self.source, self.dest, self.connection,
            self.container_config, 'request', self.database)
        self.thread1.start()

        logger.debug('Starting thread2')
        self.thread2 = OneWayThread(self.dest, self.source, self.connection,
            self.container_config, 'response', self.database)
        self.thread2.start()

        logger.debug('Joining thread1')
        self.thread1.join()
        logger.debug('Joining thread2')
        self.thread2.join()

    def run(self):
        try:
            client = docker.from_env()
            self.container = client.containers.run(self.container_config['container'], dns=['1.1.1.1'], detach=True)
            logger.info('Started: %s', self.container)
            self.container.reload()
        except Exception as err:
            logger.info(err)
            return

        try:
            self._connect_to_container()
        except Exception as err:
            logger.info(err)
            self._stop_and_remove()
            return

        self._start_and_join_threads()
        chain.delete_container_rules(self)
        self.dest.close()
        self._stop_and_remove()

    def _stop_and_remove(self):
        logger.debug(str(self.container.logs()))
        logger.info('Stopping: %s', self.container)
        self.container.stop()
        logger.info('Removing: %s', self.container)
        self.container.remove()

    def shutdown(self):
        ''' Called to shutdown the one-way threads and stop and remove the
        container. Called externally in response to a shutdown request. '''
        self.thread1.shutdown()
        self.thread2.shutdown()
        self.dest.close()
        self._stop_and_remove()
