''' The main entry point to HPotter. '''
import signal
import time
import argparse
import yaml

from src.logger import logger
from src.listen_thread import ListenThread
from src.udp_thread import UDPThread
from src.database import Database
from src import chain

# https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
class GracefulKiller:
    ''' An approach to dealing with signals. '''
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    # pylint: disable=W0613
    def exit_gracefully(self, signum, frame):
        ''' Called when SIGINT or SIGTERM sent to main process. '''
        logger.info('In exit_gracefully')
        self.kill_now = True

class HP():
    ''' The main class for HPotter '''
    def __init__(self):
        self.listen_threads = []
        self.config = {}
        self.firewall = {}
        self.database = None

    def _read_container_yaml(self, container_file):
        for container in yaml.safe_load_all(container_file):
            if 'UDP' in container:
                thread = UDPThread(container, self.database)
            else:
                thread = ListenThread(container, self.database)
            self.listen_threads.append(thread)
            thread.start()

    def add_rules(self):
        chain.add_drop_rules()
        chain.add_connection_rules()
        chain.add_dns_rules()
        chain.add_ssh_rules()

    def startup(self):
        ''' Read the configuration and start the listen threads. '''

        parser = argparse.ArgumentParser()
        parser.add_argument('--config', action='append',
            default=['config.yml'])
        parser.add_argument('--container', action='append',
            default=['containers.yml'])
        parser.add_argument('--firewall', action='append',
            default=['firewall.yml'])
        args = parser.parse_args()

        for config in args.config:
            try:
                with open(config) as config_file:
                    self.config.update(yaml.safe_load(config_file))
            except FileNotFoundError as err:
                print(err)
        
        for firewall in args.firewall:
            try:
                with open(firewall) as firewall_file:
                    self.firewall.update(yaml.safe_load(firewall_file))
            except FileNotFoundError as err:
                print(err)

        self.database = Database(self.config)
        self.database.open()

        chain.configs = self.firewall
        chain.flush_chains()
        chain.create_hpotter_chains()
        self.add_rules()

        for container in args.container:
            with open(container) as container_file:
                self._read_container_yaml(container_file)

    def shutdown(self):
        ''' Shut all the listen threads down. '''
        self.database.close()

        for listen_thread in self.listen_threads:
            logger.debug(listen_thread)
            if listen_thread.is_alive():
                logger.info('Calling ListenTread.shutdown')
                listen_thread.shutdown()

        for listen_thread in self.listen_threads:
            listen_thread.join()

        chain.flush_chains()

# pylint: disable=C0122
if "__main__" == __name__: # pragma: no cover
    hp = HP()
    hp.startup()

    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(4)

    hp.shutdown()
