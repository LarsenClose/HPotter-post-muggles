import socket
import sys
import threading
from binascii import hexlify
import paramiko
from paramiko import SSHClient
from paramiko.py3compat import u, decodebytes
import _thread
import docker

from src import tables
from src.container_thread import ContainerThread
from src.one_way_thread import OneWayThread
from src import chain
from src.logger import logger

class SSHServer(paramiko.ServerInterface):
    undertest = False
    data = (
        b"AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp"
        b"fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC"
        b"KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT"
        b"UWT10hcuO4Ks8=")
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self, connection, database):
        self.event = threading.Event()
        self.connection = connection
        self.database = database
        self.user = None
        self.password = None

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # changed so that any username/password can be used
        if username and password:
            login = tables.Credentials(username=username, password=password, \
                connection=self.connection)
            self.user = username
            self.password = password
            self.database.write(login)

            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        # print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if(username == "user") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(self, username, \
        gss_authenticated=paramiko.AUTH_FAILED, cc_file=None):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(self, username, \
        gss_auth=paramiko.AUTH_FAILED, cc_file=None):
        if gss_auth == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    # Turned off, causing problems
    def enable_auth_gssapi(self):
        return False

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    # pylint: disable=R0913
    def check_channel_pty_request(self, channel, term, width, height, \
        pixelwidth, pixelheight, modes):
        return True

class SshThread(ContainerThread):
    def __init__(self, source, connection, container_config, database):
        super().__init__(source, connection, container_config, database)
        self.source = source
        self.connection = connection
        self.container_config = container_config
        self.database = database
        self.transport = self.sshClient = self.user = self.password = None

    def start_paramiko_server(self):
        self.transport = paramiko.Transport(self.source)
        self.transport.load_server_moduli()

        # Experiment with different key sizes at:
        # http://travistidwell.com/jsencrypt/demo/
        host_key = paramiko.RSAKey(filename="RSAKey.cfg")
        self.transport.add_server_key(host_key)

        server = SSHServer(self.connection, self.database)
        self.transport.start_server(server=server)

        self.source = self.transport.accept()

        self.user = server.user
        self.password = server.password

    def create_container(self):
        client = docker.from_env()
        self.container = client.containers.run('debian:sshd', dns=['1.1.1.1'], detach=True, privileged=True)
        self.container.reload()

        # create a user, set its password, and give it sudo
        self.container.exec_run('useradd -m -s /bin/bash '+self.user)
        self.container.exec_run('usermod -aG sudo '+self.user)

        # this script exists in the docker container docker_files/sshd/Dockerfile
        # it changes the password using chpasswd but with the first argument
        self.container.exec_run('/setpasswd '+self.user+':'+self.password)
        self.container.exec_run('rm /setpasswd')

    def _connect_to_container(self):
        self.container_ip = self.container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
        self.container_gateway = self.container.attrs['NetworkSettings']['Networks']['bridge']['Gateway']
        logger.debug(self.container_ip)

        ports = self.container.attrs['NetworkSettings']['Ports']
        assert len(ports) == 1

        for port in ports.keys():
            self.container_port = int(port.split('/')[0])
            self.container_protocol = port.split('/')[1]
        logger.debug(self.container_port)
        logger.debug(self.container_protocol)

        chain.create_container_rules(self)

        self.sshClient = SSHClient()
        self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.sshClient.connect(self.container_ip, port=self.container_port, username=self.user, password=self.password)
        self.dest = self.sshClient.get_transport().open_session()
        self.dest.get_pty()
        self.dest.invoke_shell()

        logger.debug(self.dest)

    def run(self):
        self.database.write(self.connection)

        try:
            self.start_paramiko_server()
            if not self.source:
                self.transport.close()
                logger.info('no chan')
                return
        except Exception as err:
            self.transport.close()
            logger.info('Negotiation failed')
            return

        try:
            self.create_container()
            logger.info('Started: %s', self.container)
        except Exception as err:
            self._stop_and_remove()
            logger.info(err)
            return

        try:
            self._connect_to_container()
        except Exception as err:
            logger.info(err)
            self._stop_and_remove()
            return
        
        if self.source and self.dest:
            self._start_and_join_threads()

        chain.delete_container_rules(self)
        
        self._stop_and_remove()

    def _stop_and_remove(self):
        if self.transport:
            self.transport.close()
        if self.sshClient:
            self.sshClient.close()
        
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
        self._stop_and_remove()