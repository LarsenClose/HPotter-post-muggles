import unittest
from unittest.mock import mock_open, call, patch
from src.__main__ import HP, GracefulKiller
from src.udp_thread import UDPThread

class TestMain(unittest.TestCase):
    def setup(self):
        pass
    def tearDown(self):
        pass

    @patch('logging.Logger.info')
    def test_startup(self, info_mock):
        hp = HP()
        hp.startup()
        info_mock.assert_any_call('Creating SSL configuration files')
        UDPThread.shutdown(self)
        hp.shutdown()
    
    @patch('logging.Logger.info')
    def test_exit_gracefully(self, mock):
        killer = GracefulKiller()
        killer.exit_gracefully(3, 5)
        mock.assert_called_with('In exit_gracefully')


        
